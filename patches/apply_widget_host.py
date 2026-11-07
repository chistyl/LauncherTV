from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")

if "APP_WIDGET_HOST_ID" in source:
    print("Widget host patch already applied")
    raise SystemExit(0)

source = source.replace(
    "import android.app.Activity;",
    "import android.app.Activity;\nimport android.appwidget.AppWidgetHost;\nimport android.appwidget.AppWidgetHostView;\nimport android.appwidget.AppWidgetManager;\nimport android.appwidget.AppWidgetProviderInfo;"
)
source = source.replace(
    '    private static final String KEY_RECENT = "recent_apps_v1";',
    '    private static final String KEY_RECENT = "recent_apps_v1";\n'
    '    private static final String KEY_WIDGET_IDS = "home_widget_ids_v1";\n'
    '    private static final String KEY_PENDING_WIDGET = "pending_widget_id_v1";\n'
    '    private static final int APP_WIDGET_HOST_ID = 0x4B59;\n'
    '    private static final int REQUEST_WIDGET_BIND = 702;\n'
    '    private static final int REQUEST_WIDGET_CONFIGURE = 703;'
)
source = source.replace(
    '    private boolean smallCards;',
    '    private boolean smallCards;\n'
    '    private AppWidgetManager appWidgetManager;\n'
    '    private AppWidgetHost appWidgetHost;\n'
    '    private LinearLayout widgetContainer;\n'
    '    private View widgetSection;'
)
source = source.replace(
    '        language = getSharedPreferences(PREF, MODE_PRIVATE).getString(KEY_LANGUAGE, "繁體中文");\n        loadFolders(); buildHome(); loadApps();',
    '        language = getSharedPreferences(PREF, MODE_PRIVATE).getString(KEY_LANGUAGE, "繁體中文");\n'
    '        appWidgetManager = AppWidgetManager.getInstance(this);\n'
    '        appWidgetHost = new AppWidgetHost(this, APP_WIDGET_HOST_ID);\n'
    '        loadFolders(); buildHome(); loadApps();'
)
source = source.replace(
    '    @Override protected void onResume() {',
    '    @Override protected void onStart() {\n'
    '        super.onStart();\n'
    '        try { appWidgetHost.startListening(); } catch (Exception ignored) {}\n'
    '    }\n\n'
    '    @Override protected void onStop() {\n'
    '        try { appWidgetHost.stopListening(); } catch (Exception ignored) {}\n'
    '        super.onStop();\n'
    '    }\n\n'
    '    @Override protected void onResume() {'
)

old_home = '''        root.addView(top);
        TextView hint = text(tr("我的應用程式"), 17, Color.rgb(175,180,190)); hint.setPadding(0, dp(18), 0, dp(8)); root.addView(hint);
        grid = new GridView(this);'''
new_home = '''        root.addView(top);

        LinearLayout widgetHeader = new LinearLayout(this);
        widgetHeader.setGravity(Gravity.CENTER_VERTICAL);
        widgetHeader.setPadding(0, dp(10), 0, dp(5));
        TextView widgetTitle = text("小工具", 17, Color.rgb(175,180,190));
        widgetHeader.addView(widgetTitle, new LinearLayout.LayoutParams(0, dp(42), 1));
        Button addWidget = new Button(this);
        addWidget.setText("＋ 新增小工具");
        addWidget.setOnClickListener(v -> showWidgetPicker());
        widgetHeader.addView(addWidget);
        root.addView(widgetHeader);

        android.widget.HorizontalScrollView widgetScroll = new android.widget.HorizontalScrollView(this);
        widgetScroll.setHorizontalScrollBarEnabled(false);
        widgetContainer = new LinearLayout(this);
        widgetContainer.setOrientation(LinearLayout.HORIZONTAL);
        widgetContainer.setGravity(Gravity.CENTER_VERTICAL);
        widgetScroll.addView(widgetContainer, new android.widget.HorizontalScrollView.LayoutParams(-2, -1));
        widgetSection = widgetScroll;
        root.addView(widgetScroll, new LinearLayout.LayoutParams(-1, dp(178)));
        renderWidgets();

        TextView hint = text(tr("我的應用程式"), 17, Color.rgb(175,180,190)); hint.setPadding(0, dp(10), 0, dp(8)); root.addView(hint);
        grid = new GridView(this);'''
if old_home not in source:
    raise SystemExit("Home layout insertion point not found")
source = source.replace(old_home, new_home)

source = source.replace(
    'new String[]{tr("重新整理 App"),tr("切換卡片大小"),tr("新增資料夾"),tr("系統設定"),tr("HDMI 輸入"),tr("最近使用"),tr("語言"),tr("背景圖片")}',
    'new String[]{tr("重新整理 App"),tr("切換卡片大小"),tr("新增資料夾"),"新增小工具",tr("系統設定"),tr("HDMI 輸入"),tr("最近使用"),tr("語言"),tr("背景圖片")}'
)
source = source.replace(
    'else if(w==2)createFolder();else if(w==3)openSettings();else if(w==4)openHdmi();else if(w==5)showRecent();else if(w==6)showLanguageMenu(null);else chooseWallpaper();',
    'else if(w==2)createFolder();else if(w==3)showWidgetPicker();else if(w==4)openSettings();else if(w==5)openHdmi();else if(w==6)showRecent();else if(w==7)showLanguageMenu(null);else chooseWallpaper();'
)

widget_methods = r'''
    private void showWidgetPicker() {
        List<AppWidgetProviderInfo> providers;
        try { providers = appWidgetManager.getInstalledProviders(); }
        catch (Exception e) { providers = new ArrayList<>(); }
        if (providers == null || providers.isEmpty()) {
            new AlertDialog.Builder(this).setTitle("新增小工具").setMessage("此裝置目前沒有可用的小工具，或電視系統未開放 Widget 功能。Launcher 其他功能仍可正常使用。").setPositiveButton("確定", null).show();
            return;
        }
        Collections.sort(providers, (a,b) -> String.valueOf(a.loadLabel(getPackageManager())).compareToIgnoreCase(String.valueOf(b.loadLabel(getPackageManager()))));
        List<AppWidgetProviderInfo> usable = new ArrayList<>();
        List<String> labels = new ArrayList<>();
        for (AppWidgetProviderInfo info : providers) {
            if (info == null || info.provider == null) continue;
            CharSequence label;
            try { label = info.loadLabel(getPackageManager()); } catch (Exception e) { label = null; }
            String name = label == null ? info.provider.getPackageName() : label.toString();
            usable.add(info);
            labels.add(name + "  ·  " + info.provider.getPackageName());
        }
        if (usable.isEmpty()) {
            new AlertDialog.Builder(this).setTitle("新增小工具").setMessage("找不到可用的小工具提供者。").setPositiveButton("確定", null).show();
            return;
        }
        String[] items = labels.toArray(new String[0]);
        new AlertDialog.Builder(this).setTitle("選擇第三方小工具").setItems(items, (dialog, which) -> beginAddWidget(usable.get(which))).setNegativeButton("取消", null).show();
    }

    private void beginAddWidget(AppWidgetProviderInfo info) {
        if (info == null || info.provider == null) return;
        int widgetId = appWidgetHost.allocateAppWidgetId();
        getSharedPreferences(PREF, MODE_PRIVATE).edit().putInt(KEY_PENDING_WIDGET, widgetId).apply();
        try {
            boolean bound = appWidgetManager.bindAppWidgetIdIfAllowed(widgetId, info.provider);
            if (bound) {
                configureOrPlaceWidget(widgetId);
            } else {
                Intent bind = new Intent(AppWidgetManager.ACTION_APPWIDGET_BIND);
                bind.putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId);
                bind.putExtra(AppWidgetManager.EXTRA_APPWIDGET_PROVIDER, info.provider);
                startActivityForResult(bind, REQUEST_WIDGET_BIND);
            }
        } catch (Exception e) {
            discardPendingWidget(widgetId);
            Toast.makeText(this, "無法新增此小工具，可能是電視系統限制。", Toast.LENGTH_LONG).show();
        }
    }

    private void configureOrPlaceWidget(int widgetId) {
        AppWidgetProviderInfo info = appWidgetManager.getAppWidgetInfo(widgetId);
        if (info == null) { discardPendingWidget(widgetId); return; }
        if (info.configure != null) {
            try {
                Intent configure = new Intent(AppWidgetManager.ACTION_APPWIDGET_CONFIGURE);
                configure.setComponent(info.configure);
                configure.putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId);
                startActivityForResult(configure, REQUEST_WIDGET_CONFIGURE);
                return;
            } catch (Exception e) {
                Toast.makeText(this, "小工具設定畫面無法在此電視開啟，將嘗試直接加入。", Toast.LENGTH_SHORT).show();
            }
        }
        finishAddWidget(widgetId);
    }

    private void finishAddWidget(int widgetId) {
        AppWidgetProviderInfo info = appWidgetManager.getAppWidgetInfo(widgetId);
        if (info == null) { discardPendingWidget(widgetId); return; }
        JSONArray ids = readWidgetIds();
        boolean exists = false;
        for (int i=0;i<ids.length();i++) if (ids.optInt(i,-1)==widgetId) exists=true;
        if (!exists) ids.put(widgetId);
        getSharedPreferences(PREF, MODE_PRIVATE).edit().putString(KEY_WIDGET_IDS, ids.toString()).remove(KEY_PENDING_WIDGET).apply();
        renderWidgets();
        Toast.makeText(this, "小工具已加入首頁", Toast.LENGTH_SHORT).show();
    }

    private void discardPendingWidget(int widgetId) {
        try { appWidgetHost.deleteAppWidgetId(widgetId); } catch (Exception ignored) {}
        getSharedPreferences(PREF, MODE_PRIVATE).edit().remove(KEY_PENDING_WIDGET).apply();
    }

    private JSONArray readWidgetIds() {
        String raw = getSharedPreferences(PREF, MODE_PRIVATE).getString(KEY_WIDGET_IDS, "[]");
        try { return new JSONArray(raw); } catch (Exception e) { return new JSONArray(); }
    }

    private void saveWidgetIds(JSONArray ids) {
        getSharedPreferences(PREF, MODE_PRIVATE).edit().putString(KEY_WIDGET_IDS, ids.toString()).apply();
    }

    private void renderWidgets() {
        if (widgetContainer == null) return;
        widgetContainer.removeAllViews();
        JSONArray ids = readWidgetIds();
        JSONArray valid = new JSONArray();
        for (int i=0;i<ids.length();i++) {
            int id = ids.optInt(i,-1);
            if (id < 0) continue;
            AppWidgetProviderInfo info;
            try { info = appWidgetManager.getAppWidgetInfo(id); } catch (Exception e) { info = null; }
            if (info == null) {
                try { appWidgetHost.deleteAppWidgetId(id); } catch (Exception ignored) {}
                continue;
            }
            try {
                AppWidgetHostView hostView = appWidgetHost.createView(this, id, info);
                hostView.setAppWidget(id, info);
                hostView.setFocusable(true);
                hostView.setFocusableInTouchMode(true);
                int minW = Math.max(240, info.minWidth);
                int minH = Math.max(120, info.minHeight);
                int width = Math.min(520, Math.max(300, minW));
                int height = Math.min(260, Math.max(160, minH));
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(width), dp(height));
                lp.setMargins(0, 0, dp(14), 0);
                hostView.setBackground(makeCardBackground(false));
                hostView.setPadding(dp(4),dp(4),dp(4),dp(4));
                hostView.setOnLongClickListener(v -> {
                    new AlertDialog.Builder(this).setTitle("移除小工具？").setMessage("只會從首頁移除，不會解除安裝提供小工具的 APP。").setNegativeButton("取消", null).setPositiveButton("移除", (d,w) -> removeWidget(id)).show();
                    return true;
                });
                widgetContainer.addView(hostView, lp);
                valid.put(id);
            } catch (Exception e) {
                try { appWidgetHost.deleteAppWidgetId(id); } catch (Exception ignored) {}
            }
        }
        if (valid.length() != ids.length()) saveWidgetIds(valid);
        if (widgetSection != null) widgetSection.setVisibility(valid.length() == 0 ? View.GONE : View.VISIBLE);
    }

    private void removeWidget(int widgetId) {
        JSONArray old = readWidgetIds();
        JSONArray next = new JSONArray();
        for (int i=0;i<old.length();i++) {
            int id = old.optInt(i,-1);
            if (id == widgetId) continue;
            if (id >= 0) next.put(id);
        }
        saveWidgetIds(next);
        try { appWidgetHost.deleteAppWidgetId(widgetId); } catch (Exception ignored) {}
        renderWidgets();
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_WIDGET_BIND || requestCode == REQUEST_WIDGET_CONFIGURE) {
            int widgetId = getSharedPreferences(PREF, MODE_PRIVATE).getInt(KEY_PENDING_WIDGET, -1);
            if (widgetId >= 0) {
                if (resultCode == RESULT_OK && appWidgetManager.getAppWidgetInfo(widgetId) != null) {
                    if (requestCode == REQUEST_WIDGET_BIND) configureOrPlaceWidget(widgetId);
                    else finishAddWidget(widgetId);
                } else {
                    discardPendingWidget(widgetId);
                    Toast.makeText(this, "小工具新增已取消或未獲授權。", Toast.LENGTH_SHORT).show();
                }
            }
            return;
        }
        if(requestCode==701 && resultCode==RESULT_OK && data!=null && data.getData()!=null){ Uri u=data.getData(); try{getContentResolver().takePersistableUriPermission(u,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception ignored){} getSharedPreferences(PREF,MODE_PRIVATE).edit().putString(KEY_BG,u.toString()).apply(); buildHome(); loadApps(); }
    }

'''
anchor = '    private class AppEntry { String label,pkg,activity; Drawable icon,banner; }'
if anchor not in source:
    raise SystemExit("Widget method insertion point not found")
source = source.replace(anchor, widget_methods + anchor)

# Replace the original wallpaper-only result handler with the combined handler above.
old_result = '    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) { super.onActivityResult(requestCode,resultCode,data); if(requestCode==701 && resultCode==RESULT_OK && data!=null && data.getData()!=null){ Uri u=data.getData(); try{getContentResolver().takePersistableUriPermission(u,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception ignored){} getSharedPreferences(PREF,MODE_PRIVATE).edit().putString(KEY_BG,u.toString()).apply(); buildHome(); loadApps(); } }'
if old_result not in source:
    raise SystemExit("Original wallpaper onActivityResult handler not found")
source = source.replace(old_result, "")

if "APP_WIDGET_HOST_ID" not in source or "showWidgetPicker()" not in source or "renderWidgets()" not in source:
    raise SystemExit("Widget host patch validation failed")

path.write_text(source, encoding="utf-8")
print("Applied Android AppWidgetHost implementation to", path)
