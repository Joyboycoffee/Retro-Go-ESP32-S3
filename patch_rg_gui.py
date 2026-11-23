# Patch rg_gui.c
with open('retro-go/components/retro-go/rg_gui.c', 'r', encoding='utf-8') as f:
    c = f.read()

target_rg = '''    if (battery.present)
    {
        char bat_txt[8];
        snprintf(bat_txt, sizeof(bat_txt), "%d%%", (int)battery.level);
        rg_rect_t bat_rect = TEXT_RECT(bat_txt, 0);
        right += bat_rect.width + 3;
        rg_gui_draw_text(-right, 0, 0, bat_txt, C_SILVER, gui.screen_buffer ? C_TRANSPARENT : C_BLACK, 0);

        right += 22;

        int width = 16;
        int height = icon_height;
        int width_fill = width / 100.f * battery.level;
        int x_pos = -right;
        int y_pos = icon_top;

        rg_color_t color_fill = (battery.level > 20 ? (battery.level > 40 ? C_FOREST_GREEN : C_ORANGE) : C_RED);
        rg_color_t color_border = C_SILVER;
        rg_color_t color_empty = C_BLACK;

        rg_gui_draw_rect(x_pos, y_pos, width + 2, height, 1, color_border, C_NONE);
        rg_gui_draw_rect(x_pos + width + 2, y_pos + 2, 2, height - 4, 0, 0, color_border);
        rg_gui_draw_rect(x_pos + 1, y_pos + 1, width_fill, height - 2, 0, 0, color_fill);
        rg_gui_draw_rect(x_pos + 1 + width_fill, y_pos + 1, width - width_fill, height - 2, 0, 0, color_empty);
    }

    if (network.state > RG_NETWORK_DISCONNECTED)
    {
        right += 22;

        int width = 16;
        int height = icon_height;
        int seg_width = (width - 2 - 2) / 3;
        int seg_height = height / 3;
        int x_pos = -right;
        int y_pos = icon_top + height;

        rg_color_t color_fill = (network.state == RG_NETWORK_CONNECTED) ? C_GREEN : C_NONE;
        rg_color_t color_border = (network.state == RG_NETWORK_CONNECTED) ? C_SILVER : C_DIM_GRAY;

        rg_gui_draw_rect(x_pos, y_pos - seg_height * 1, seg_width, seg_height * 1, 1, color_border, color_fill);
        x_pos += seg_width + 2;
        rg_gui_draw_rect(x_pos, y_pos - seg_height * 2, seg_width, seg_height * 2, 1, color_border, color_fill);
        x_pos += seg_width + 2;
        rg_gui_draw_rect(x_pos, y_pos - seg_height * 3, seg_width, seg_height * 3, 1, color_border, color_fill);
    }'''

replacement_rg = '''    if (battery.present)
    {
        // Embedded Battery Percentage inside Battery Icon Case (Saves horizontal space & prevents text collision)
        char bat_txt[8];
        snprintf(bat_txt, sizeof(bat_txt), "%d%%", (int)battery.level);
        rg_rect_t bat_rect = TEXT_RECT(bat_txt, 0);

        int width = RG_MAX(24, bat_rect.width + 4);
        int height = icon_height;
        int width_fill = (width * (int)battery.level) / 100;

        right += width + 6;
        int x_pos = -right;
        int y_pos = icon_top;

        rg_color_t color_fill = (battery.level > 20 ? (battery.level > 40 ? C_FOREST_GREEN : C_ORANGE) : C_RED);
        rg_color_t color_border = C_SILVER;
        rg_color_t color_empty = C_BLACK;

        // Battery outer border and positive terminal tip
        rg_gui_draw_rect(x_pos, y_pos, width + 2, height, 1, color_border, C_NONE);
        rg_gui_draw_rect(x_pos + width + 2, y_pos + 2, 2, height - 4, 0, 0, color_border);

        // Fill levels
        rg_gui_draw_rect(x_pos + 1, y_pos + 1, width_fill, height - 2, 0, 0, color_fill);
        rg_gui_draw_rect(x_pos + 1 + width_fill, y_pos + 1, width - width_fill, height - 2, 0, 0, color_empty);

        // Render percentage digits directly centered INSIDE the battery icon
        int text_x = x_pos + 1 + (width - bat_rect.width) / 2;
        int text_y = y_pos + (height - bat_rect.height) / 2;
        rg_gui_draw_text(text_x, text_y, 0, bat_txt, C_WHITE, C_TRANSPARENT, 0);
    }

    if (network.state > RG_NETWORK_DISCONNECTED)
    {
        // Retro Wi-Fi Signal Arcs/Bars
        right += 18;
        int width = 16;
        int height = icon_height;
        int x_pos = -right;
        int y_pos = icon_top;
        int cx = x_pos + width / 2;
        int by = y_pos + height - 2;

        rg_color_t color_active = (network.state == RG_NETWORK_CONNECTED) ? C_GREEN : C_SILVER;
        rg_color_t color_dim = C_DIM_GRAY;

        // Bottom Wi-Fi Broadcast Dot
        rg_gui_draw_rect(cx - 1, by - 1, 2, 2, 0, 0, color_active);

        // Middle Wi-Fi Broadcast Arc
        rg_color_t col_mid = (network.state == RG_NETWORK_CONNECTED) ? color_active : color_dim;
        rg_gui_draw_rect(cx - 3, by - 4, 6, 1, 0, 0, col_mid);
        rg_gui_draw_rect(cx - 4, by - 3, 1, 1, 0, 0, col_mid);
        rg_gui_draw_rect(cx + 3, by - 3, 1, 1, 0, 0, col_mid);

        // Outer Wi-Fi Broadcast Arc
        rg_color_t col_outer = (network.state == RG_NETWORK_CONNECTED) ? color_active : color_dim;
        rg_gui_draw_rect(cx - 6, by - 7, 12, 1, 0, 0, col_outer);
        rg_gui_draw_rect(cx - 7, by - 6, 1, 2, 0, 0, col_outer);
        rg_gui_draw_rect(cx + 6, by - 6, 1, 2, 0, 0, col_outer);
    }'''

assert target_rg in c, "target_rg not found in rg_gui.c"
c = c.replace(target_rg, replacement_rg)
with open('retro-go/components/retro-go/rg_gui.c', 'w', encoding='utf-8') as f:
    f.write(c)
print("rg_gui.c patched successfully")

# Patch launcher/main/gui.c
with open('retro-go/launcher/main/gui.c', 'r', encoding='utf-8') as f:
    gc = f.read()

target_gc = '''    if (tab->banner)
        rg_gui_draw_image(LOGO_WIDTH + 1, offset + 8, 0, HEADER_HEIGHT - 8, false, tab->banner);
    else
        rg_gui_draw_text(LOGO_WIDTH + 8, offset + 8, 0, tab->desc, gui.theme->foreground, C_TRANSPARENT, RG_TEXT_BIGGER);'''

replacement_gc = '''    if (tab->banner)
        rg_gui_draw_image(LOGO_WIDTH + 1, offset + 14, 0, HEADER_HEIGHT - 14, false, tab->banner);
    else
        rg_gui_draw_text(LOGO_WIDTH + 8, offset + 14, 0, tab->desc, gui.theme->foreground, C_TRANSPARENT, RG_TEXT_BIGGER);'''

assert target_gc in gc, "target_gc not found in launcher/main/gui.c"
gc = gc.replace(target_gc, replacement_gc)
with open('retro-go/launcher/main/gui.c', 'w', encoding='utf-8') as f:
    f.write(gc)
print("launcher/main/gui.c patched successfully")
