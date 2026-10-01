package com.qbank.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {

    private static final int REQ_EXPORT = 1001;
    private static final int REQ_IMPORT = 1002;

    private WebView webView;
    private String pendingExportJson;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);

        setSystemBarsDark(false);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(248, 250, 252));

        webView = new WebView(this);
        webView.setBackgroundColor(Color.TRANSPARENT);

        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setAllowFileAccess(true);
        webView.getSettings().setAllowContentAccess(false);
        webView.setVerticalScrollBarEnabled(false);
        webView.setHorizontalScrollBarEnabled(false);

        webView.addJavascriptInterface(new AndroidBridge(), "AndroidBridge");
        webView.setWebViewClient(new WebViewClient());

        root.addView(
                webView,
                new FrameLayout.LayoutParams(
                        FrameLayout.LayoutParams.MATCH_PARENT,
                        FrameLayout.LayoutParams.MATCH_PARENT
                )
        );

        root.setOnApplyWindowInsetsListener((v, insets) -> {
            int top;
            int bottom;

            if (Build.VERSION.SDK_INT >= 30) {
                Insets bars = insets.getInsets(
                        WindowInsets.Type.statusBars() |
                        WindowInsets.Type.navigationBars()
                );
                top = bars.top;
                bottom = bars.bottom;
            } else {
                top = insets.getSystemWindowInsetTop();
                bottom = insets.getSystemWindowInsetBottom();
            }

            final String js =
                    "document.documentElement.style.setProperty('--android-safe-top','"
                            + top + "px');" +
                    "document.documentElement.style.setProperty('--android-safe-bottom','"
                            + bottom + "px');";

            webView.post(() -> webView.evaluateJavascript(js, null));
            return insets;
        });

        setContentView(root);

        webView.loadUrl("file:///android_asset/index.html");
    }

    private void setSystemBarsDark(boolean dark) {
        int bg = Color.parseColor(dark ? "#0F172A" : "#F8FAFC");

        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);

        int flags = 0;
        if (!dark) {
            flags |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            if (Build.VERSION.SDK_INT >= 26) {
                flags |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            }
        }

        getWindow().getDecorView().setSystemUiVisibility(flags);

        if (webView != null) {
            webView.setBackgroundColor(bg);
        }
    }

    @Override
    public void onBackPressed() {
        if (webView == null) {
            super.onBackPressed();
            return;
        }

        webView.evaluateJavascript(
                "(function(){try{return window.qbankBack?window.qbankBack():false;}catch(e){return false;}})();",
                value -> {
                    if ("false".equals(value) || "null".equals(value)) {
                        if (webView.canGoBack()) {
                            webView.goBack();
                        } else {
                            finish();
                        }
                    }
                }
        );
    }

    private class AndroidBridge {

        @JavascriptInterface
        public void setSystemBarsDark(boolean dark) {
            runOnUiThread(() -> setSystemBarsDark(dark));
        }

        @JavascriptInterface
        public void exportJson(String json, String fileName) {
            pendingExportJson = json;

            Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("application/json");
            intent.putExtra(Intent.EXTRA_TITLE, fileName);

            startActivityForResult(intent, REQ_EXPORT);
        }

        @JavascriptInterface
        public void importJson() {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("application/json");

            startActivityForResult(intent, REQ_IMPORT);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (resultCode != RESULT_OK || data == null) {
            return;
        }

        Uri uri = data.getData();
        if (uri == null) {
            return;
        }

        try {
            if (requestCode == REQ_EXPORT && pendingExportJson != null) {
                try (OutputStream out = getContentResolver().openOutputStream(uri)) {
                    if (out != null) {
                        out.write(pendingExportJson.getBytes(StandardCharsets.UTF_8));
                        out.flush();
                    }
                }
                pendingExportJson = null;

            } else if (requestCode == REQ_IMPORT) {
                StringBuilder sb = new StringBuilder();

                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(
                                getContentResolver().openInputStream(uri),
                                StandardCharsets.UTF_8
                        )
                )) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        sb.append(line).append('\n');
                    }
                }

                String jsonLiteral = JSONObject.quote(sb.toString());

                webView.evaluateJavascript(
                        "window.applyImportedBackup(" + jsonLiteral + ");",
                        null
                );
            }

        } catch (Exception e) {
            webView.evaluateJavascript(
                    "alert(" + JSONObject.quote(
                            "Backup operation failed: " + e.getMessage()
                    ) + ");",
                    null
            );
        }
    }
}
