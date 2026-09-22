package com.thefxtrader.botzw;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Button;

public class MainActivity extends Activity {

    private LinearLayout root;

    private TextView connection;
    private TextView marketStatus;
    private TextView signal;
    private TextView strength;
    private TextView confirmations;
    private TextView entry;
    private TextView stopLoss;
    private TextView tp1;
    private TextView tp2;
    private TextView invalidation;
    private TextView news;
    private TextView dataAge;
    private TextView systemStatus;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        buildUI();
    }

    private TextView text(String value, int size, boolean bold) {
        TextView v = new TextView(this);
        v.setText(value);
        v.setTextColor(Color.WHITE);
        v.setTextSize(size);
        v.setPadding(24, 18, 24, 18);

        if (bold) {
            v.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        }

        return v;
    }

    private TextView card(String value) {
        TextView v = text(value, 16, false);
        v.setBackgroundColor(Color.rgb(30, 30, 30));
        return v;
    }

    private TextView section(String value) {
        TextView v = text(value, 14, true);
        v.setPadding(24, 28, 24, 12);
        return v;
    }

    private void buildUI() {

        ScrollView scroll = new ScrollView(this);

        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(18, 25, 18, 25);
        root.setBackgroundColor(Color.BLACK);

        TextView title = text(
                "THE_FX.TRADER.BOT.ZW",
                25,
                true
        );
        title.setGravity(Gravity.CENTER);
        root.addView(title);

        TextView subtitle = text(
                "Professional Market Signal System",
                14,
                false
        );
        subtitle.setGravity(Gravity.CENTER);
        root.addView(subtitle);

        root.addView(section("SYSTEM STATUS"));

        connection = card("🟡  CONNECTION: CHECKING");
        root.addView(connection);

        systemStatus = card(
                "System: STARTING\n" +
                "Signal engine: READY\n" +
                "Automatic trading: DISABLED"
        );
        root.addView(systemStatus);

        root.addView(section("PRIMARY MARKET"));

        marketStatus = card("🟡  XAUUSD: CHECKING");
        root.addView(marketStatus);

        TextView xau = text("XAUUSD — GOLD", 23, true);
        xau.setGravity(Gravity.CENTER);
        root.addView(xau);

        dataAge = card("Last market update: —");
        root.addView(dataAge);

        root.addView(section("CURRENT SIGNAL"));

        signal = card("WAIT");
        signal.setGravity(Gravity.CENTER);
        signal.setTextSize(30);
        signal.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        root.addView(signal);

        strength = card("Strength: 0/10");
        root.addView(strength);

        confirmations = card("Confirmations: 0");
        root.addView(confirmations);

        root.addView(section("SIGNAL LEVELS"));

        entry = card("Entry / Reference: —");
        root.addView(entry);

        stopLoss = card("Stop Loss: —");
        root.addView(stopLoss);

        tp1 = card("TP1: —");
        root.addView(tp1);

        tp2 = card("TP2: —");
        root.addView(tp2);

        invalidation = card("Invalidation: —");
        root.addView(invalidation);

        root.addView(section("NEWS INTELLIGENCE"));

        news = card(
                "News risk: LOW\n" +
                "News bias: NEUTRAL\n" +
                "Fresh XAUUSD news: 0"
        );
        root.addView(news);

        root.addView(section("MARKET MONITOR"));

        TextView markets = card(
                "XAUUSD: PRIMARY\n" +
                "BTCUSD: CHECKING\n" +
                "STEP INDEX: CHECKING\n" +
                "VOLATILITY 75: CHECKING\n" +
                "Other configured markets: MONITORING"
        );
        root.addView(markets);

        root.addView(section("SAFETY"));

        TextView safety = card(
                "Signal-only mode: ENABLED\n" +
                "Trade execution: DISABLED\n" +
                "Automatic trading: DISABLED\n" +
                "Candle-close protection: ENABLED\n" +
                "Duplicate protection: ENABLED\n" +
                "Cooldown protection: ENABLED"
        );
        root.addView(safety);

        root.addView(section("ACTIONS"));

        Button history = new Button(this);
        history.setText("SIGNAL HISTORY");
        root.addView(history);

        Button alerts = new Button(this);
        alerts.setText("ALERT SETTINGS");
        root.addView(alerts);

        Button stop = new Button(this);
        stop.setText("EMERGENCY STOP");
        root.addView(stop);

        stop.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                signal.setText("STOPPED");

                connection.setText(
                        "🔴  CONNECTION: STOPPED"
                );

                marketStatus.setText(
                        "⚪  XAUUSD: MONITORING STOPPED"
                );

                systemStatus.setText(
                        "System: EMERGENCY STOP\n" +
                        "Signal generation: STOPPED\n" +
                        "Automatic trading: DISABLED"
                );
            }
        });

        TextView footer = text(
                "© 2026 THE_FX.TRADER.BOT.ZW — All Rights Reserved\n" +
                "+263 78 455 2452",
                12,
                false
        );

        footer.setGravity(Gravity.CENTER);
        root.addView(footer);

        scroll.addView(root);
        setContentView(scroll);
    }
}
