package com.zonaeducacional.postscriptum;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.view.WindowManager;
import android.widget.Toast;
import org.json.JSONObject;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Offline-only host: all requests must match the packaged asset allowlist. */
public final class MainActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private static final String START = "https://" + HOST + "/index.html";
    private static final int SAVE_DOCUMENT = 101, OPEN_DOCUMENT = 102;
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private WebView web;
    private ValueCallback<Uri[]> chooser;
    private String pendingData, pendingToken;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        // Avoid exposing intimate text in screenshots or the recent-apps thumbnail.
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE);
        getWindow().setStatusBarColor(Color.rgb(204,222,210));
        getWindow().setNavigationBarColor(Color.rgb(204,222,210));
        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(255,251,212));
        setContentView(web);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true); // Only URIs explicitly chosen through ACTION_OPEN_DOCUMENT.
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        WebView.setWebContentsDebuggingEnabled(false);
        web.addJavascriptInterface(new DocumentBridge(), "PostScriptumAndroid");
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !local(request.getUrl());
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri=request.getUrl();
                if (!"GET".equals(request.getMethod()) || !local(uri)) return blocked();
                String path=uri.getPath();
                if (path==null || path.equals("/")) path="/index.html";
                String asset=path.substring(1);
                if (!allowedAsset(asset)) return blocked();
                try {
                    InputStream stream=getAssets().open("www/"+asset);
                    Map<String,String> headers=new HashMap<>();
                    headers.put("Cache-Control","no-store");
                    headers.put("X-Content-Type-Options","nosniff");
                    return new WebResourceResponse(mime(asset),"UTF-8",200,"OK",headers,stream);
                } catch(Exception e) { return blocked(); }
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (chooser!=null) chooser.onReceiveValue(null);
                chooser=callback;
                Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                intent.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"application/json","text/plain","application/octet-stream"});
                try { startActivityForResult(intent,OPEN_DOCUMENT); }
                catch(Exception e) { chooser.onReceiveValue(null);chooser=null;Toast.makeText(MainActivity.this,"Seletor de arquivos indisponível.",Toast.LENGTH_LONG).show(); }
                return true;
            }
        });
        web.setDownloadListener((url,userAgent,contentDisposition,mimeType,length)->Toast.makeText(this,"Use os botões de exportação do caderno.",Toast.LENGTH_LONG).show());
        web.loadUrl(START);
    }
    private static boolean local(Uri uri) {
        return "https".equals(uri.getScheme()) && HOST.equals(uri.getHost()) && uri.getPort()==-1 && uri.getUserInfo()==null;
    }
    private static boolean allowedAsset(String name) {
        return name.equals("index.html") || name.equals("style.css") || name.equals("app.js") || name.equals("manifest.webmanifest") || name.equals("icon.svg") || name.equals("icon-192.png") || name.equals("icon-512.png") || name.matches("fonts/(lora-(regular|medium|italic)|caveat)\\.ttf");
    }
    private static String mime(String name) {
        if(name.endsWith(".html"))return "text/html";
        if(name.endsWith(".css"))return "text/css";
        if(name.endsWith(".js"))return "application/javascript";
        if(name.endsWith(".ttf"))return "font/ttf";
        if(name.endsWith(".svg"))return "image/svg+xml";
        if(name.endsWith(".png"))return "image/png";
        return "application/manifest+json";
    }
    private static WebResourceResponse blocked() {
        return new WebResourceResponse("text/plain","UTF-8",403,"Forbidden",new HashMap<>(),new ByteArrayInputStream(new byte[0]));
    }
    public final class DocumentBridge {
        @JavascriptInterface public void saveDocument(String data,String name,String type,String token) {
            runOnUiThread(()->{
                if (pendingToken!=null) { reply(token,false,"Outra exportação está em andamento."); return; }
                if (data==null || data.length()>32*1024*1024 || token==null || !token.matches("[a-zA-Z0-9-]{1,100}") || !("application/json".equals(type)||"text/plain;charset=utf-8".equals(type))) {
                    reply(token,false,"Arquivo de exportação inválido ou muito grande."); return;
                }
                pendingData=data;pendingToken=token;
                Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType(type.startsWith("text/plain")?"text/plain":"application/json");
                intent.putExtra(Intent.EXTRA_TITLE,name.replaceAll("[^a-zA-Z0-9._-]","-"));
                try { startActivityForResult(intent,SAVE_DOCUMENT); }
                catch(Exception e) { pendingData=null;pendingToken=null;reply(token,false,"Não foi possível abrir o seletor de arquivos."); }
            });
        }
    }
    private void reply(String token,boolean success,String message) {
        if(token==null)return;
        runOnUiThread(()->{if(web!=null)web.evaluateJavascript("window.postScriptumDocumentResult("+JSONObject.quote(token)+","+success+","+JSONObject.quote(message)+")",null);});
    }
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode==OPEN_DOCUMENT) {
            if(chooser!=null){chooser.onReceiveValue(resultCode==RESULT_OK&&data!=null&&data.getData()!=null?new Uri[]{data.getData()}:null);chooser=null;}return;
        }
        if(requestCode==SAVE_DOCUMENT) {
            final String text=pendingData,token=pendingToken;
            pendingData=null;pendingToken=null;
            if(resultCode!=RESULT_OK||data==null||data.getData()==null||text==null){reply(token,false,"Exportação cancelada. Seu caderno foi preservado.");return;}
            final Uri uri=data.getData();
            io.execute(()->{
                try(OutputStream stream=getContentResolver().openOutputStream(uri,"w")) {
                    if(stream==null)throw new IllegalStateException();
                    stream.write(text.getBytes(StandardCharsets.UTF_8));stream.flush();
                }catch(Exception e){reply(token,false,"Não foi possível concluir a gravação do arquivo. Tente novamente.");return;}
                reply(token,true,"Arquivo salvo no local escolhido.");
            });
        }
    }
    @Override public void onBackPressed() {
        web.evaluateJavascript("location.hash",value->{
            if(value!=null&&!value.equals("\"#timeline\"")&&!value.equals("\"\""))web.evaluateJavascript("document.querySelector('[data-view=timeline]').click()",null);
            else new AlertDialog.Builder(this).setTitle("Fechar o caderno?").setMessage("Confira se a gravação foi concluída antes de sair.").setNegativeButton("Continuar",null).setPositiveButton("Fechar",(dialog,which)->finish()).show();
        });
    }
    @Override protected void onPause() {
        if(web!=null)web.evaluateJavascript("document.dispatchEvent(new Event('postscriptum-pause'))",null);
        super.onPause();
    }
    @Override protected void onDestroy() {
        if(chooser!=null){chooser.onReceiveValue(null);chooser=null;}
        io.shutdown();
        if(web!=null){web.removeJavascriptInterface("PostScriptumAndroid");web.destroy();web=null;}
        super.onDestroy();
    }
}
