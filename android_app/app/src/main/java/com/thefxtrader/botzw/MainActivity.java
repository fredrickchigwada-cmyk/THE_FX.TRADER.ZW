package com.thefxtrader.botzw;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.graphics.Color;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {

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

    private final Handler handler = new Handler(Looper.getMainLooper());

    private final ExecutorService executor =
            Executors.newSingleThreadExecutor();

    private static final String API =
            "http://127.0.0.1:8765/snapshot";

    private static final String STOP_API =
            "http://127.0.0.1:8765/stop";

    private final Runnable refreshTask = new Runnable() {
        @Override
        public void run() {
            fetchSnapshot();

            handler.postDelayed(
                    this,
                    2000
            );
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        buildUI();

        handler.post(refreshTask);
    }

    private TextView text(
            String value,
            int size,
            boolean bold
    ) {
        TextView v = new TextView(this);

        v.setText(value);
        v.setTextSize(size);
        v.setTextColor(Color.WHITE);
        v.setPadding(20, 14, 20, 14);

        if (bold) {
            v.setTypeface(
                    android.graphics.Typeface.DEFAULT_BOLD
            );
        }

        return v;
    }

    private TextView card(String value) {
        TextView v = text(value, 16, false);

        v.setBackgroundColor(
                Color.rgb(28, 28, 28)
        );

        v.setPadding(22, 22, 22, 22);

        return v;
    }

    private TextView section(String value) {
        TextView v = text(value, 14, true);

        v.setTextColor(
                Color.LTGRAY
        );

        return v;
    }

    private void buildUI() {

        ScrollView scroll = new ScrollView(this);

        LinearLayout root =
                new LinearLayout(this);

        root.setOrientation(
                LinearLayout.VERTICAL
        );

        root.setPadding(
                18,
                18,
                18,
                18
        );

        root.setBackgroundColor(
                Color.BLACK
        );

        TextView title = text(
                "THE_FX.TRADER.BOT.ZW",
                25,
                true
        );

        title.setGravity(
                Gravity.CENTER
        );

        root.addView(title);

        TextView subtitle = text(
                "LIVE SIGNAL INTELLIGENCE",
                13,
                false
        );

        subtitle.setGravity(
                Gravity.CENTER
        );

        root.addView(subtitle);

        connection = card(
                "🟡 CONNECTION: CHECKING"
        );

        root.addView(connection);

        systemStatus = card(
                "System: CHECKING\n" +
                "Signal generation: CHECKING\n" +
                "Automatic trading: DISABLED"
        );

        root.addView(systemStatus);

        root.addView(
                section("PRIMARY MARKET")
        );

        TextView xau = text(
                "XAUUSD — GOLD",
                23,
                true
        );

        root.addView(xau);

        marketStatus = card(
                "🟡 XAUUSD: CHECKING"
        );

        root.addView(marketStatus);

        dataAge = card(
                "Data age: --"
        );

        root.addView(dataAge);

        root.addView(
                section("CURRENT SIGNAL")
        );

        signal = card(
                "Signal: WAIT"
        );

        root.addView(signal);

        strength = card(
                "Strength: -- / 10"
        );

        root.addView(strength);

        confirmations = card(
                "Confirmations: --"
        );

        root.addView(confirmations);

        entry = card(
                "Entry / Reference: --"
        );

        root.addView(entry);

        stopLoss = card(
                "Stop Loss: --"
        );

        root.addView(stopLoss);

        tp1 = card(
                "TP1: --"
        );

        root.addView(tp1);

        tp2 = card(
                "TP2: --"
        );

        root.addView(tp2);

        invalidation = card(
                "Invalidation: --"
        );

        root.addView(invalidation);

        root.addView(
                section("NEWS INTELLIGENCE")
        );

        news = card(
                "News: CHECKING"
        );

        root.addView(news);

        root.addView(
                section("SYSTEM SAFETY")
        );

        TextView safety = card(
                "Signal-only mode: ENABLED\n" +
                "Automatic trading: DISABLED\n" +
                "Emergency protection: ENABLED\n" +
                "Duplicate protection: ENABLED\n" +
                "Candle-close protection: ENABLED"
        );

        root.addView(safety);

        Button stop =
                new Button(this);

        stop.setText(
                "EMERGENCY STOP"
        );

        stop.setOnClickListener(
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        emergencyStop();
                    }
                }
        );

        root.addView(stop);

        TextView footer = text(
                "© 2026 THE_FX.TRADER.BOT.ZW — All Rights Reserved\n" +
                "+263 78 455 2452",
                12,
                false
        );

        footer.setGravity(
                Gravity.CENTER
        );

        root.addView(footer);

        scroll.addView(root);

        setContentView(scroll);
    }

    private void fetchSnapshot() {

        executor.execute(
                new Runnable() {
                    @Override
                    public void run() {

                        HttpURLConnection connection =
                                null;

                        try {

                            URL url =
                                    new URL(API);

                            connection =
                                    (HttpURLConnection)
                                            url.openConnection();

                            connection.setRequestMethod(
                                    "GET"
                            );

                            connection.setConnectTimeout(
                                    1500
                            );

                            connection.setReadTimeout(
                                    1500
                            );

                            int code =
                                    connection.getResponseCode();

                            if (code != 200) {
                                throw new Exception(
                                        "HTTP " + code
                                );
                            }

                            InputStream input =
                                    connection.getInputStream();

                            BufferedReader reader =
                                    new BufferedReader(
                                            new InputStreamReader(
                                                    input
                                            )
                                    );

                            StringBuilder response =
                                    new StringBuilder();

                            String line;

                            while (
                                    (line = reader.readLine())
                                            != null
                            ) {
                                response.append(line);
                            }

                            reader.close();

                            final JSONObject json =
                                    new JSONObject(
                                            response.toString()
                                    );

                            runOnUiThread(
                                    new Runnable() {
                                        @Override
                                        public void run() {
                                            updateDashboard(
                                                    json
                                            );
                                        }
                                    }
                            );

                        } catch (Exception e) {

                            runOnUiThread(
                                    new Runnable() {
                                        @Override
                                        public void run() {

                                            connection.setText(
                                                    "🔴 CONNECTION: BACKEND OFFLINE"
                                            );

                                            marketStatus.setText(
                                                    "⚪ XAUUSD: WAITING FOR TERMUX BACKEND"
                                            );

                                            systemStatus.setText(
                                                    "System: BACKEND NOT CONNECTED\n" +
                                                    "Signal generation: WAITING\n" +
                                                    "Automatic trading: DISABLED"
                                            );
                                        }
                                    }
                            );

                        } finally {

                            if (connection != null) {
                                connection.disconnect();
                            }
                        }
                    }
                }
        );
    }

    private void updateDashboard(
            JSONObject json
    ) {

        try {

            boolean running =
                    json.optBoolean(
                            "running",
                            false
                    );

            boolean connected =
                    json.optBoolean(
                            "connected",
                            false
                    );

            boolean healthy =
                    json.optBoolean(
                            "healthy",
                            false
                    );

            boolean stale =
                    json.optBoolean(
                            "stale",
                            true
                    );

            boolean rateLimited =
                    json.optBoolean(
                            "rate_limited",
                            false
                    );

            String primary =
                    json.optString(
                            "primary_market",
                            "XAUUSD"
                    );

            String timeframe =
                    json.optString(
                            "timeframe",
                            "M1"
                    );

            long lastEpoch =
                    json.optLong(
                            "last_epoch",
                            0
                    );

            String lastPrice =
                    json.optString(
                            "last_price",
                            "--"
                    );

            String newsRisk =
                    json.optString(
                            "news_risk",
                            "LOW"
                    );

            String newsBias =
                    json.optString(
                            "news_bias",
                            "NEUTRAL"
                    );

            int newsItems =
                    json.optInt(
                            "news_items",
                            0
                    );

            if (connected && healthy) {

                connection.setText(
                        "🟢 CONNECTION: CONNECTED"
                );

            } else if (rateLimited) {

                connection.setText(
                        "🟡 CONNECTION: RATE LIMITED"
                );

            } else {

                connection.setText(
                        "🟡 CONNECTION: CONNECTING"
                );
            }

            if (running) {

                systemStatus.setText(
                        "System: " +
                                (healthy
                                        ? "HEALTHY"
                                        : "CHECKING") +
                                "\n" +
                                "Signal generation: " +
                                (running
                                        ? "ACTIVE"
                                        : "STOPPED") +
                                "\n" +
                                "Automatic trading: DISABLED"
                );

            } else {

                systemStatus.setText(
                        "System: STOPPED\n" +
                        "Signal generation: STOPPED\n" +
                        "Automatic trading: DISABLED"
                );
            }

            marketStatus.setText(
                    "XAUUSD: " +
                            (connected
                                    ? "MONITORING"
                                    : "WAITING") +
                            "\n" +
                            "Timeframe: " +
                            timeframe +
                            "\n" +
                            "Price: " +
                            lastPrice
            );

            if (lastEpoch > 0) {

                long now =
                        System.currentTimeMillis()
                                / 1000L;

                long age =
                        Math.max(
                                0,
                                now - lastEpoch
                        );

                dataAge.setText(
                        "Data age: " +
                                age +
                                " seconds"
                );

            } else {

                dataAge.setText(
                        "Data age: --"
                );
            }

            JSONObject signalObject =
                    json.optJSONObject(
                            "signal"
                    );

            if (signalObject != null) {

                signal.setText(
                        "Signal: " +
                                signalObject.optString(
                                        "direction",
                                        "WAIT"
                                )
                );

                strength.setText(
                        "Strength: " +
                                signalObject.optInt(
                                        "strength",
                                        0
                                ) +
                                " / 10"
                );

                confirmations.setText(
                        "Confirmations: " +
                                signalObject.optInt(
                                        "confirmations",
                                        0
                                )
                );

                entry.setText(
                        "Entry / Reference: " +
                                signalObject.optString(
                                        "entry",
                                        "--"
                                )
                );

                stopLoss.setText(
                        "Stop Loss: " +
                                signalObject.optString(
                                        "stop_loss",
                                        "--"
                                )
                );

                tp1.setText(
                        "TP1: " +
                                signalObject.optString(
                                        "tp1",
                                        "--"
                                )
                );

                tp2.setText(
                        "TP2: " +
                                signalObject.optString(
                                        "tp2",
                                        "--"
                                )
                );

                invalidation.setText(
                        "Invalidation: " +
                                signalObject.optString(
                                        "invalidation",
                                        "--"
                                )
                );

            } else {

                signal.setText(
                        "Signal: WAIT"
                );

                strength.setText(
                        "Strength: -- / 10"
                );

                confirmations.setText(
                        "Confirmations: --"
                );
            }

            news.setText(
                    "Risk: " +
                            newsRisk +
                            "\n" +
                            "Bias: " +
                            newsBias +
                            "\n" +
                            "Fresh XAUUSD items: " +
                            newsItems
            );

        } catch (Exception e) {

            connection.setText(
                    "🟡 CONNECTION: DATA ERROR"
            );
        }
    }

    private void emergencyStop() {

        executor.execute(
                new Runnable() {
                    @Override
                    public void run() {

                        HttpURLConnection conn =
                                null;

                        try {

                            URL url =
                                    new URL(STOP_API);

                            conn =
                                    (HttpURLConnection)
                                            url.openConnection();

                            conn.setRequestMethod(
                                    "POST"
                            );

                            conn.setConnectTimeout(
                                    1500
                            );

                            conn.setReadTimeout(
                                    1500
                            );

                            conn.getResponseCode();

                            runOnUiThread(
                                    new Runnable() {
                                        @Override
                                        public void run() {

                                            signal.setText(
                                                    "Signal: STOPPED"
                                            );

                                            connection.setText(
                                                    "🔴 CONNECTION: STOPPED"
                                            );

                                            marketStatus.setText(
                                                    "⚪ XAUUSD: MONITORING STOPPED"
                                            );

                                            systemStatus.setText(
                                                    "System: EMERGENCY STOP\n" +
                                                    "Signal generation: STOPPED\n" +
                                                    "Automatic trading: DISABLED"
                                            );
                                        }
                                    }
                            );

                        } catch (Exception e) {

                            runOnUiThread(
                                    new Runnable() {
                                        @Override
                                        public void run() {

                                            systemStatus.setText(
                                                    "System: STOP COMMAND FAILED\n" +
                                                    "Automatic trading: DISABLED"
                                            );
                                        }
                                    }
                            );

                        } finally {

                            if (conn != null) {
                                conn.disconnect();
                            }
                        }
                    }
                }
        );
    }

    @Override
    protected void onDestroy() {

        handler.removeCallbacks(
                refreshTask
        );

        executor.shutdownNow();

        super.onDestroy();
    }
}
