package com.qbank.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
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

        getWindow().setStatusBarColor(Color.parseColor("#F8FAFC"));
        getWindow().setNavigationBarColor(Color.parseColor("#F8FAFC"));

        getWindow().getDecorView().setSystemUiVisibility(
                android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR |
                android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
        );

        FrameLayout root = new FrameLayout(this);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#F8FAFC"));

        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setAllowFileAccess(true);
        webView.getSettings().setAllowContentAccess(false);

        webView.setVerticalScrollBarEnabled(false);
        webView.setHorizontalScrollBarEnabled(false);

        webView.addJavascriptInterface(new AndroidBridge(), "AndroidBridge");
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);

                int statusId = getResources().getIdentifier(
                        "status_bar_height", "dimen", "android");
                int navId = getResources().getIdentifier(
                        "navigation_bar_height", "dimen", "android");

                int top = statusId > 0
                        ? getResources().getDimensionPixelSize(statusId) : 0;
                int bottom = navId > 0
                        ? getResources().getDimensionPixelSize(navId) : 0;

                String js =
                        "document.documentElement.style.setProperty('--android-safe-top','"
                        + top + "px');" +
                        "document.documentElement.style.setProperty('--android-safe-bottom','"
                        + bottom + "px');";

                view.evaluateJavascript(js, null);
            }
        });

        root.addView(webView, new FrameLayout.LayoutParams(-1, -1));
        setContentView(root);

        int statusId = getResources().getIdentifier(
                "status_bar_height", "dimen", "android");
        int navId = getResources().getIdentifier(
                "navigation_bar_height", "dimen", "android");

        int top = statusId > 0
                ? getResources().getDimensionPixelSize(statusId) : 0;
        int bottom = navId > 0
                ? getResources().getDimensionPixelSize(navId) : 0;

        root.setPadding(0, top, 0, bottom);

        int statusId = getResources().getIdentifier(
                "status_bar_height", "dimen", "android"
        );
        int navId = getResources().getIdentifier(
                "navigation_bar_height", "dimen", "android"
        );

        int status = statusId > 0
                ? getResources().getDimensionPixelSize(statusId)
                : 0;

        int nav = navId > 0
                ? getResources().getDimensionPixelSize(navId)
                : 0;

        String js =
                "document.documentElement.style.setProperty('--android-safe-top','"
                        + status + "px');" +
                "document.documentElement.style.setProperty('--android-safe-bottom','"
                        + nav + "px');";

        webView.post(() -> webView.evaluateJavascript(js, null));

        webView.loadUrl("file:///android_asset/index.html");
    }

    private void applySystemBars(boolean dark) {
        int bg = Color.parseColor(dark ? "#0F172A" : "#F8FAFC");

        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);

        int flags = 0;

        if (!dark) {
            flags |= android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            flags |= android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
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
                "(function(){" +
                "try{" +
                "return window.qbankBack ? window.qbankBack() : false;" +
                "}catch(e){return false;}" +
                "})()",
                value -> {
                    if ("false".equals(value) || "null".equals(value)) {
                        finish();
                    }
                }
        );
    }

    private class AndroidBridge {

        @JavascriptInterface
        public void setSystemBarsDark(boolean dark) {
            runOnUiThread(() -> applySystemBars(dark));
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
    protected void onActivityResult(
            int requestCode,
            int resultCode,
            Intent data
    ) {
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

                try (OutputStream out =
                             getContentResolver().openOutputStream(uri)) {

                    if (out != null) {
                        out.write(
                                pendingExportJson.getBytes(
                                        StandardCharsets.UTF_8
                                )
                        );
                        out.flush();
                    }
                }

                pendingExportJson = null;

            } else if (requestCode == REQ_IMPORT) {

                StringBuilder sb = new StringBuilder();

                try (BufferedReader reader =
                             new BufferedReader(
                                     new InputStreamReader(
                                             getContentResolver()
                                                     .openInputStream(uri),
                                             StandardCharsets.UTF_8
                                     )
                             )) {

                    String line;

                    while ((line = reader.readLine()) != null) {
                        sb.append(line).append('\n');
                    }
                }

                String quoted = JSONObject.quote(sb.toString());

                webView.evaluateJavascript(
                        "window.applyImportedBackup(" +
                        quoted +
                        ");",
                        null
                );
            }

        } catch (Exception e) {

            webView.evaluateJavascript(
                    "alert(" +
                    JSONObject.quote(
                            "Backup operation failed: " +
                            e.getMessage()
                    ) +
                    ");",
                    null
            );
        }
    }
}
