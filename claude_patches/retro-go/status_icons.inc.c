// =============================================================================
//  Retro-Go status bar icons (beige theme)  --  replaces rg_gui_draw_icons()
//
//  * Wi-Fi  : dot + three 90-degree (quarter-circle) arcs radiating outwards
//             - Connected: Vibrant Green with signal strength arcs based on RSSI
//             - Connecting / Searching: Blue blinking radar wave animation
//             - Disconnected: Muted dim gray
//  * Battery: VERTICAL cell, terminal nub on top, segmented fill, drawn in beige
//  * Percent: drawn to the LEFT of the battery, never inside / overlapping it
//  * Top padding: top_y = 5px so icons and text never hug the screen bezel
// =============================================================================

#define STATUS_COLOR        C_BEIGE   /* 0xF7BB, the Retro-Go theme beige            */
#define STATUS_COLOR_DIM    0x7BCD    /* beige at 50% - inactive Wi-Fi tiers          */
#ifndef RG_STATUS_WARN_LOW_BATT
#define RG_STATUS_WARN_LOW_BATT 1     /* 1 = fill turns red at <=15% (set 0 = always beige) */
#endif
#define STATUS_ICON_MAX     24

// With a screen buffer we can skip transparent pixels. Without one the pixels go
// straight to the LCD, so "transparent" must be a real colour (the bar is black).
static inline rg_color_t status_bg(void)
{
    return gui.screen_buffer ? C_TRANSPARENT : C_BLACK;
}

static void status_blit(int x, int y, int w, int h, const uint16_t *px)
{
    rg_gui_copy_buffer(x, y, w, h, w * 2, px, gui.screen_buffer != NULL);
}

// ---- Battery (vertical) ------------------------------------------------------
static void status_battery_size(int bar_h, int *w, int *h)
{
    int total_h = RG_MIN(RG_MAX(bar_h - 1, 10), 20);
    int body_w = RG_MIN(RG_MAX((total_h * 6) / 10, 7), 12);
    *w = body_w;
    *h = total_h;
}

static void status_draw_battery(int x, int y, int w, int h, int level)
{
    uint16_t px[STATUS_ICON_MAX * STATUS_ICON_MAX];
    const uint16_t bg = status_bg();
    const int nub_h = 2;
    const int nub_w = (w / 2) & ~1;                 // even width, centred
    const int nub_x = (w - nub_w) / 2;
    const int body_y = nub_h;                       // body starts below the nub
    const int body_h = h - nub_h;

    level = RG_MIN(RG_MAX(level, 0), 100);
    uint16_t fill = STATUS_COLOR;
#if RG_STATUS_WARN_LOW_BATT
    if (level <= 15)
        fill = C_RED;
#endif

    for (int i = 0; i < w * h; i++)
        px[i] = bg;

    // Terminal nub (top)
    for (int yy = 0; yy < nub_h; yy++)
        for (int xx = nub_x; xx < nub_x + nub_w; xx++)
            px[yy * w + xx] = STATUS_COLOR;

    // 1px outline of the cell body
    for (int xx = 0; xx < w; xx++)
    {
        px[body_y * w + xx] = STATUS_COLOR;
        px[(h - 1) * w + xx] = STATUS_COLOR;
    }
    for (int yy = body_y; yy < h; yy++)
    {
        px[yy * w + 0] = STATUS_COLOR;
        px[yy * w + (w - 1)] = STATUS_COLOR;
    }

    // Segmented fill - grows from the bottom
    const int in_x = 2, in_w = w - 4;               // 1px air gap inside the outline
    const int in_top = body_y + 2, in_h = body_h - 4;
    if (in_w > 0 && in_h > 0)
    {
        const int nseg = (in_h >= 11) ? 4 : (in_h >= 8) ? 3 : 2;
        const int gap = 1;
        const int seg_h = (in_h - (nseg - 1) * gap) / nseg;
        const int used = nseg * seg_h + (nseg - 1) * gap;
        const int pad = (in_h - used) / 2;           // centre the stack vertically
        int filled = (level * nseg + 50) / 100;
        if (level > 0 && filled == 0)
            filled = 1;                              // never show an empty cell while alive

        for (int s = 0; s < filled; s++)             // s = 0 is the bottom segment
        {
            int seg_bottom = in_top + in_h - pad - 1 - s * (seg_h + gap);
            for (int yy = seg_bottom - seg_h + 1; yy <= seg_bottom; yy++)
                for (int xx = in_x; xx < in_x + in_w; xx++)
                    px[yy * w + xx] = fill;
        }
    }
    status_blit(x, y, w, h, px);
}

// ---- Wi-Fi (dot + 3 quarter-circle arcs) --------------------------------------
static void status_wifi_size(int bar_h, int *w, int *h)
{
    int hh = RG_MIN(RG_MAX(bar_h - 1, 9), 16);
    int r3 = hh - 2;
    int half = (int)(r3 * 0.7071f + 0.999f);
    *w = half * 2 + 3;
    *h = hh;
}

static void status_draw_wifi(int x, int y, int w, int h, int state, int rssi)
{
    uint16_t px[STATUS_ICON_MAX * STATUS_ICON_MAX];
    const uint16_t bg = status_bg();
    const float cx = (w - 1) * 0.5f;
    const float cy = (float)(h - 2);                 // arcs radiate from just above the bottom
    const float r3 = (float)(h - 2);
    const float radius[3] = {r3 * 0.43f, r3 * 0.71f, r3};   // evenly spaced tiers
    const float thick = (r3 <= 8.0f) ? 0.50f : 0.62f;       // half line-width: 1px lines on tiny bars
    const float dot_r2 = (r3 <= 8.0f) ? 1.0f : 2.0f;        // plus-shaped dot on tiny bars

    uint16_t dot_color = bg;
    uint16_t active_color = bg;
    uint16_t dim_color = bg;
    int num_bars = 0;

    if (state == RG_NETWORK_CONNECTED)
    {
        // Connected: Vibrant Emerald Green
        dot_color    = 0x27E6;
        active_color = 0x27E6;
        dim_color    = 0x0A42; // Muted dark green for unlit arcs

        if (rssi != 0)
        {
            if (rssi < -80)      num_bars = 1;
            else if (rssi < -68) num_bars = 2;
            else                 num_bars = 3;
        }
        else
        {
            num_bars = 3;
        }
    }
    else if (state == RG_NETWORK_CONNECTING)
    {
        // Connecting / Searching: Blue blinking radar wave animation
        bool blink = ((rg_system_timer() / 300000) & 1) != 0;
        int wave = (rg_system_timer() / 200000) % 4; // 0=dot, 1=1 arc, 2=2 arcs, 3=3 arcs
        dot_color    = blink ? 0x249F : 0x01D3;      // Dodger Blue blinking
        active_color = 0x249F;
        dim_color    = 0x0112;                       // Dark blue for unlit wave
        num_bars     = wave;
    }
    else // Disconnected
    {
        dot_color    = 0x7BEF; // Dim gray
        active_color = 0x7BEF;
        dim_color    = 0x39E7;
        num_bars     = 0;
    }

    for (int yy = 0; yy < h; yy++)
    {
        for (int xx = 0; xx < w; xx++)
        {
            float dx = xx - cx;
            float dy = cy - yy;                      // up is positive
            float d2 = dx * dx + dy * dy;
            float d = sqrtf(d2);
            uint16_t c = bg;

            if (d2 <= dot_r2)                        // the dot
            {
                c = dot_color;
            }
            else if (dy > 0.0f && fabsf(dx) <= dy + 0.35f)   // inside the +-45deg cone = quarter circle
            {
                for (int k = 0; k < 3; k++)
                {
                    if (fabsf(d - radius[k]) <= thick)
                    {
                        c = (k < num_bars) ? active_color : dim_color;
                        break;
                    }
                }
            }
            px[yy * w + xx] = c;
        }
    }
    status_blit(x, y, w, h, px);
}

void rg_gui_draw_icons(void)
{
    rg_battery_t battery = rg_input_read_battery();
    rg_network_t network = rg_network_get_info();
    rg_rect_t txt = TEXT_RECT("00:00", 0);
    const int bar_height = txt.height;
    const rg_color_t text_bg = status_bg();
    const int top_y = 5;                             // 5px padding from top edge (no hugging the bezel!)
    int right = gui.margins.right + 5;                // 5px padding from right edge

    // 1) Battery: vertical cell at the far right, percentage on its LEFT
    if (battery.present)
    {
        int level = (int)(battery.level + 0.5f);
        level = RG_MIN(RG_MAX(level, 0), 100);

        int bw, bh;
        status_battery_size(bar_height, &bw, &bh);
        right += bw;
        status_draw_battery(-right, top_y + RG_MAX(0, (bar_height - bh) / 2), bw, bh, level);

        char bat_txt[8];
        snprintf(bat_txt, sizeof(bat_txt), "%d%%", level);
        rg_rect_t bat_rect = TEXT_RECT(bat_txt, 0);
        right += 3 + bat_rect.width;                       // 3px gap, then the text box
        rg_gui_draw_text(-right, top_y, 0, bat_txt, STATUS_COLOR, text_bg, 0);
    }

    // 2) Wi-Fi arcs
    if (network.state > RG_NETWORK_DISABLED)
    {
        int ww, wh;
        status_wifi_size(bar_height, &ww, &wh);
        right += 6 + ww;
        status_draw_wifi(-right, top_y + RG_MAX(0, (bar_height - wh) / 2), ww, wh,
                         network.state, network.rssi);
    }

    // 3) Clock text
    if (gui.show_clock)
    {
        char buffer[16];
        time_t time_sec = time(NULL);
        struct tm *time = localtime(&time_sec);

        if (gui.clock_12hr)
        {
            int hour = time->tm_hour % 12;
            if (hour == 0) hour = 12;
            const char *am_pm = (time->tm_hour >= 12) ? "PM" : "AM";
            sprintf(buffer, "%d:%02d %s", hour, time->tm_min, am_pm);
        }
        else
        {
            sprintf(buffer, "%02d:%02d", time->tm_hour, time->tm_min);
        }

        rg_rect_t clock_txt = TEXT_RECT(buffer, 0);
        right += 6 + clock_txt.width;
        rg_gui_draw_text(-right, top_y, 0, buffer, STATUS_COLOR, text_bg, 0);
    }
}
