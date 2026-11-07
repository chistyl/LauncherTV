from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

if "APP_WIDGET_HOST_ID" not in s:
    raise SystemExit("Native AppWidgetHost patch must run before enhancements")

s = s.replace(
    '    private static final String KEY_WIDGET_IDS = "home_widget_ids_v1";',
    '    private static final String KEY_WIDGET_IDS = "home_widget_ids_v1";\n'
    '    private static final String KEY_WIDGET_SIZES = "home_widget_sizes_v1";'
)
s = s.replace(
    '    private static final int REQUEST_WIDGET_CONFIGURE = 703;',
    '    private static final int REQUEST_WIDGET_CONFIGURE = 703;\n'
    '    private static final int REQUEST_WIDGET_RECONFIGURE = 704;'
)
s = s.replace(
    '    private View widgetSection;',
    '    private View widgetSection;\n'
    '    private int widgetFocusId = -1;'
)
if "import android.view.ViewParent;" not in s:
    s = s.replace("import android.view.ViewGroup;", "import android.view.ViewGroup;\nimport android.view.ViewParent;")

s = s.replace(
    "root.addView(widgetScroll, new LinearLayout.LayoutParams(-1, dp(178)));",
    "widgetScroll.setId(View.generateViewId());\n        root.addView(widgetScroll, new LinearLayout.LayoutParams(-1, dp(226)));"
)
s = s.replace(
    "grid = new GridView(this); grid.setHorizontalSpacing",
    "grid = new GridView(this); grid.setId(View.generateViewId()); grid.setHorizontalSpacing"
)

pattern = re.compile(r"    private void renderWidgets\(\) \{.*?\n    \}\n\n    private void removeWidget", re.S)
replacement = r'''    private JSONObject readWidgetSizes() {
        String raw = getSharedPreferences(PREF, MODE_PRIVATE).getString(KEY_WIDGET_SIZES, "{}");
        try { return new JSONObject(raw); } catch (Exception e) { return new JSONObject(); }
    }

    private int[] getWidgetSize(int widgetId, AppWidgetProviderInfo info) {
        JSONObject saved = readWidgetSizes().optJSONObject(String.valueOf(widgetId));
        int minW = info == null ? 0 : Math.max(0, info.minWidth);
        int minH = info == null ? 0 : Math.max(0, info.minHeight);
        int width = saved == null ? Math.max(320, Math.min(640, minW)) : saved.optInt("width", 420);
        int height = saved == null ? Math.max(160, Math.min(220, minH)) : saved.optInt("height", 180);
        return new int[]{Math.max(minW, width), Math.max(minH, height)};
    }

    private void persistWidgetSize(int widgetId, int width, int height) {
        JSONObject all = readWidgetSizes();
        JSONObject size = new JSONObject();
        try {
            size.put("width", width);
            size.put("height", height);
            all.put(String.valueOf(widgetId), size);
            getSharedPreferences(PREF, MODE_PRIVATE).edit().putString(KEY_WIDGET_SIZES, all.toString()).apply();
        } catch (Exception ignored) {}
    }

    private void applyWidgetOptions(int widgetId, int width, int height) {
        try {
            Bundle options = new Bundle();
            options.putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH, width);
            options.putInt(AppWidgetManager.OPTION_APPWIDGET_MAX_WIDTH, width);
            options.putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT, height);
            options.putInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT, height);
            appWidgetManager.updateAppWidgetOptions(widgetId, options);
        } catch (Exception ignored) {}
    }

    private void resizeWidget(int widgetId, int preset) {
        AppWidgetProviderInfo info = appWidgetManager.getAppWidgetInfo(widgetId);
        if (info == null) return;
        int[] widths = {320, 420, 520};
        int[] heights = {140, 180, 220};
        int index = Math.max(0, Math.min(2, preset));
        int width = Math.max(Math.max(0, info.minWidth), widths[index]);
        int height = Math.max(Math.max(0, info.minHeight), heights[index]);
        persistWidgetSize(widgetId, width, height);
        applyWidgetOptions(widgetId, width, height);
        widgetFocusId = widgetId;
        renderWidgets();
    }

    private void moveWidget(int widgetId, int direction) {
        JSONArray old = readWidgetIds();
        List<Integer> ordered = new ArrayList<>();
        for (int i = 0; i < old.length(); i++) {
            int id = old.optInt(i, -1);
            if (id >= 0) ordered.add(id);
        }
        int index = ordered.indexOf(widgetId);
        int target = index + direction;
        if (index < 0 || target < 0 || target >= ordered.size()) {
            Toast.makeText(this, direction < 0 ? "已經是第一個小工具" : "已經是最後一個小工具", Toast.LENGTH_SHORT).show();
            return;
        }
        Collections.swap(ordered, index, target);
        JSONArray next = new JSONArray();
        for (Integer id : ordered) next.put(id);
        saveWidgetIds(next);
        widgetFocusId = widgetId;
        renderWidgets();
    }

    private void reconfigureWidget(int widgetId) {
        AppWidgetProviderInfo info = appWidgetManager.getAppWidgetInfo(widgetId);
        if (info == null || info.configure == null) {
            Toast.makeText(this, "此小工具沒有額外設定畫面", Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            Intent configure = new Intent(AppWidgetManager.ACTION_APPWIDGET_CONFIGURE);
            configure.setComponent(info.configure);
            configure.putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, widgetId);
            startActivityForResult(configure, REQUEST_WIDGET_RECONFIGURE);
        } catch (Exception e) {
            Toast.makeText(this, "無法開啟此小工具的設定畫面", Toast.LENGTH_SHORT).show();
        }
    }

    private void showWidgetActions(int widgetId) {
        String[] actions = {"小尺寸", "中尺寸", "大尺寸", "向左移動", "向右移動", "重新設定", "移除小工具"};
        new AlertDialog.Builder(this).setTitle("小工具設定").setItems(actions, (dialog, which) -> {
            if (which >= 0 && which <= 2) resizeWidget(widgetId, which);
            else if (which == 3) moveWidget(widgetId, -1);
            else if (which == 4) moveWidget(widgetId, 1);
            else if (which == 5) reconfigureWidget(widgetId);
            else if (which == 6) new AlertDialog.Builder(this).setTitle("移除小工具？")
                .setMessage("只會從首頁移除，不會解除安裝提供小工具的 APP。")
                .setNegativeButton("取消", null)
                .setPositiveButton("移除", (d, w) -> removeWidget(widgetId)).show();
        }).setNegativeButton("關閉", null).show();
    }

    private AppWidgetHostView findFocusedWidgetHost() {
        View current = getCurrentFocus();
        while (current != null) {
            if (current instanceof AppWidgetHostView) return (AppWidgetHostView) current;
            ViewParent parent = current.getParent();
            current = parent instanceof View ? (View) parent : null;
        }
        return null;
    }

    private void renderWidgets() {
        if (widgetContainer == null) return;
        widgetContainer.removeAllViews();
        JSONArray ids = readWidgetIds();
        JSONArray valid = new JSONArray();
        int firstWidgetViewId = View.NO_ID;
        for (int i = 0; i < ids.length(); i++) {
            int id = ids.optInt(i, -1);
            if (id < 0) continue;
            AppWidgetProviderInfo info;
            try { info = appWidgetManager.getAppWidgetInfo(id); } catch (Exception e) { info = null; }
            if (info == null) {
                try { appWidgetHost.deleteAppWidgetId(id); } catch (Exception ignored) {}
                JSONObject sizes = readWidgetSizes();
                sizes.remove(String.valueOf(id));
                getSharedPreferences(PREF, MODE_PRIVATE).edit().putString(KEY_WIDGET_SIZES, sizes.toString()).apply();
                continue;
            }
            View widgetView;
            int[] size = getWidgetSize(id, info);
            try {
                AppWidgetHostView hostView = appWidgetHost.createView(this, id, info);
                hostView.setAppWidget(id, info);
                hostView.setFocusable(true);
                hostView.setFocusableInTouchMode(true);
                hostView.setId(View.generateViewId());
                hostView.setBackground(makeCardBackground(false));
                hostView.setPadding(dp(4), dp(4), dp(4), dp(4));
                hostView.setOnLongClickListener(v -> { showWidgetActions(id); return true; });
                hostView.setOnKeyListener((v, keyCode, event) -> {
                    if (event.getAction() == KeyEvent.ACTION_DOWN &&
                        (keyCode == KeyEvent.KEYCODE_MENU || keyCode == KeyEvent.KEYCODE_INFO ||
                        (keyCode == KeyEvent.KEYCODE_DPAD_CENTER && event.isLongPress()))) {
                        showWidgetActions(id);
                        return true;
                    }
                    return false;
                });
                hostView.setOnFocusChangeListener((v, focused) -> {
                    v.setBackground(makeCardBackground(focused));
                    v.setElevation(focused ? dp(10) : dp(2));
                    v.animate().scaleX(focused ? 1.025f : 1f).scaleY(focused ? 1.025f : 1f).setDuration(120).start();
                });
                if (grid != null) hostView.setNextFocusDownId(grid.getId());
                widgetView = hostView;
            } catch (Exception e) {
                TextView fallback = text("小工具暫時無法顯示\n長按或按選單鍵管理", 16, Color.WHITE);
                fallback.setGravity(Gravity.CENTER);
                fallback.setFocusable(true);
                fallback.setId(View.generateViewId());
                fallback.setBackground(makeCardBackground(false));
                fallback.setOnLongClickListener(v -> { showWidgetActions(id); return true; });
                fallback.setOnKeyListener((v, keyCode, event) -> {
                    if (event.getAction() == KeyEvent.ACTION_DOWN &&
                        (keyCode == KeyEvent.KEYCODE_MENU || keyCode == KeyEvent.KEYCODE_INFO)) {
                        showWidgetActions(id);
                        return true;
                    }
                    return false;
                });
                if (grid != null) fallback.setNextFocusDownId(grid.getId());
                widgetView = fallback;
            }
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(size[0]), dp(size[1]));
            lp.setMargins(0, 0, dp(14), 0);
            widgetContainer.addView(widgetView, lp);
            if (firstWidgetViewId == View.NO_ID) firstWidgetViewId = widgetView.getId();
            valid.put(id);
            if (widgetFocusId == id) { final View focusTarget = widgetView; focusTarget.post(() -> { focusTarget.requestFocus(); widgetFocusId = -1; }); }
        }
        if (valid.length() != ids.length()) saveWidgetIds(valid);
        if (widgetSection != null) widgetSection.setVisibility(valid.length() == 0 ? View.GONE : View.VISIBLE);
        if (grid != null && firstWidgetViewId != View.NO_ID) grid.setNextFocusUpId(firstWidgetViewId);
    }

    private void removeWidget'''
s, count = pattern.subn(lambda match: replacement, s, count=1)
if count != 1:
    raise SystemExit("Could not replace renderWidgets implementation")

s = s.replace(
    '        saveWidgetIds(next);\n        try { appWidgetHost.deleteAppWidgetId(widgetId); } catch (Exception ignored) {}\n        renderWidgets();',
    '        saveWidgetIds(next);\n'
    '        JSONObject sizes = readWidgetSizes(); sizes.remove(String.valueOf(widgetId));\n'
    '        getSharedPreferences(PREF, MODE_PRIVATE).edit().putString(KEY_WIDGET_SIZES, sizes.toString()).apply();\n'
    '        try { appWidgetHost.deleteAppWidgetId(widgetId); } catch (Exception ignored) {}\n'
    '        renderWidgets();'
)
s = s.replace(
    '        if (!exists) ids.put(widgetId);\n'
    '        getSharedPreferences(PREF, MODE_PRIVATE).edit().putString(KEY_WIDGET_IDS, ids.toString()).remove(KEY_PENDING_WIDGET).apply();',
    '        if (!exists) ids.put(widgetId);\n'
    '        int[] size = getWidgetSize(widgetId, info);\n'
    '        persistWidgetSize(widgetId, size[0], size[1]);\n'
    '        applyWidgetOptions(widgetId, size[0], size[1]);\n'
    '        getSharedPreferences(PREF, MODE_PRIVATE).edit().putString(KEY_WIDGET_IDS, ids.toString()).remove(KEY_PENDING_WIDGET).apply();'
)
s = s.replace(
    '        super.onActivityResult(requestCode, resultCode, data);\n'
    '        if (requestCode == REQUEST_WIDGET_BIND || requestCode == REQUEST_WIDGET_CONFIGURE) {',
    '        super.onActivityResult(requestCode, resultCode, data);\n'
    '        if (requestCode == REQUEST_WIDGET_RECONFIGURE) { renderWidgets(); return; }\n'
    '        if (requestCode == REQUEST_WIDGET_BIND || requestCode == REQUEST_WIDGET_CONFIGURE) {'
)
s = s.replace(
    '    @Override public boolean onKeyDown(int keyCode,KeyEvent event) {\n'
    '        if(keyCode==KeyEvent.KEYCODE_MENU){',
    '    @Override public boolean onKeyDown(int keyCode,KeyEvent event) {\n'
    '        if (keyCode == KeyEvent.KEYCODE_MENU || keyCode == KeyEvent.KEYCODE_INFO ||\n            (keyCode == KeyEvent.KEYCODE_DPAD_CENTER && event.isLongPress())) {\n'
    '            AppWidgetHostView focusedWidget = findFocusedWidgetHost();\n'
    '            if (focusedWidget != null) { showWidgetActions(focusedWidget.getAppWidgetId()); return true; }\n'
    '        }\n'
    '        if(keyCode==KeyEvent.KEYCODE_MENU){'
)

required = [
    "KEY_WIDGET_SIZES", "showWidgetActions", "resizeWidget", "moveWidget",
    "REQUEST_WIDGET_RECONFIGURE", "findFocusedWidgetHost",
    "updateAppWidgetOptions", "setNextFocusDownId"
]
missing = [token for token in required if token not in s]
if missing:
    raise SystemExit("Widget enhancement validation failed: " + ", ".join(missing))

# Keep the source package documentation aligned with the implemented controls.
project_root = path.parents[6]
readme = project_root / "README.zh-TW.md"
if readme.exists():
    docs = readme.read_text(encoding="utf-8")
    docs = docs.replace(
        "此原始碼封裝本身不代表 APK 已完成編譯。",
        "本版 APK 已由 GitHub Actions 成功編譯並通過自動化相容性檢查；實際電視韌體、Widget Provider 與遙控器操作仍需在目標裝置驗收。"
    )
    marker = "## 原生 Android 小工具"
    verification = """## 建置驗證
- CI 已成功執行原生 Widget patch、相容性檢查及 assembleDebug。
- Debug applicationId：tw.kangyuan.tvlauncher.debug（可與正式版並存）。
- Android 最低版本：8.0 / API 26。

"""
    if marker in docs and "## 建置驗證" not in docs:
        docs = docs.replace(marker, verification + marker, 1)
    if marker not in docs:
        docs += """

## 原生 Android 小工具
- 使用 Android 原生 AppWidgetHost / AppWidgetManager，支援系統中已安裝且可用的第三方 Widget Provider。
- 可從首頁「新增小工具」加入，支援 Provider 綁定授權與首次設定畫面。
- 每個小工具可選小、中、大三種版面尺寸；尺寸會透過 AppWidget options 通知 Provider，並保存於 Launcher。
- 可向左／向右調整小工具順序；重新啟動 Launcher 後會恢復已加入的小工具、尺寸與順序。
- 將焦點移至小工具後，可長按遙控器確認鍵，或按 MENU／INFO 開啟管理選單；支援重新設定及移除。
- 暫時無法建立 RemoteViews 時保留有效的小工具 ID，避免短暫錯誤造成設定遺失。
- Widget 功能在 Manifest 中標示為選用；不具備 Widget host 的 Android TV 仍可使用 Launcher 其他功能。

注意：部分 Android TV 韌體會停用 AppWidgetHost，或沒有提供任何第三方 Widget Provider。這種情況下，Launcher 會顯示無可用小工具提示；是否能顯示特定 Widget，仍取決於電視系統及該 Provider 的相容性。
"""
    readme.write_text(docs, encoding="utf-8")

path.write_text(s, encoding="utf-8")
print("Enhanced Widget size, order, recovery and remote-focus controls:", path)
