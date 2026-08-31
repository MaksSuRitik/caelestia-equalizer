#!/bin/bash
POS_FILE="/home/regis/Загрузки/MusicStandaloneApp/.saved_pos"

if pgrep -f "MusicStandaloneApp/main.py" > /dev/null; then
    # Парсим координаты прямо из Hyprland перед тем как убить процесс
    hyprctl clients | awk '/Standalone Music App/{flag=1} flag && /at:/{print $2, $3; flag=0}' | tr -d ',' > "$POS_FILE"
    pkill -f "MusicStandaloneApp/main.py"
else
    python /home/regis/Загрузки/MusicStandaloneApp/main.py &
    APP_PID=$!
    sleep 0.6

    # Если файл с координатами существует и не пустой — двигаем туда
    if [ -s "$POS_FILE" ]; then
        read -r X Y < "$POS_FILE"
        /usr/bin/hyprctl dispatch movewindowpixel "exact $X $Y,pid:$APP_PID"
    else
        # Дефолтная позиция, если приложение запускается вообще первый раз
        /usr/bin/hyprctl dispatch movewindowpixel "exact 20 60,pid:$APP_PID"
    fi
fi
