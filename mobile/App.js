import { useMemo, useRef, useState } from "react";
import { ActivityIndicator, Platform, Pressable, StatusBar as RNStatusBar, StyleSheet, Text, View } from "react-native";
import { Audio } from "expo-av";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, useSafeAreaInsets } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";

const APP_URL = process.env.EXPO_PUBLIC_APP_URL || "http://172.20.10.2:8080";

function apiMessage(text, fallback) {
  const raw = String(text || "").trim();
  if (!raw) return fallback;
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed?.detail === "string" && parsed.detail.trim()) return parsed.detail.trim();
  } catch (_err) {
    /* plain text */
  }
  return raw;
}

function tellWeb(webRef, payload) {
  webRef.current?.injectJavaScript(
    `window.dispatchEvent(new CustomEvent("secondshift-native",{detail:${JSON.stringify(payload)}}));true;`,
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AppScreen />
    </SafeAreaProvider>
  );
}

function AppScreen() {
  const insets = useSafeAreaInsets();
  const webRef = useRef(null);
  const recordingRef = useRef(null);
  const extraRef = useRef({});
  const [error, setError] = useState("");
  const [tick, setTick] = useState(0);
  const source = useMemo(() => ({ uri: `${APP_URL}/?v=ss27` }), [tick]);
  const padTop = insets.top || (Platform.OS === "android" ? RNStatusBar.currentHeight || 28 : 0);
  const padBottom = insets.bottom || (Platform.OS === "android" ? 48 : 0);

  function retry() {
    setError("");
    setTick((n) => n + 1);
  }

  async function startNativeMic(extra) {
    extraRef.current = extra || {};
    const permission = await Audio.requestPermissionsAsync();
    if (!permission.granted) {
      throw new Error("Allow the microphone for Expo Go, then try again.");
    }
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
    });
    if (recordingRef.current) {
      try {
        await recordingRef.current.stopAndUnloadAsync();
      } catch (_err) {
        /* already stopped */
      }
      recordingRef.current = null;
    }
    const { recording } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
    recordingRef.current = recording;
  }

  async function cancelNativeMic() {
    const recording = recordingRef.current;
    recordingRef.current = null;
    if (!recording) {
      tellWeb(webRef, { type: "mic-cancelled" });
      return;
    }
    try {
      await recording.stopAndUnloadAsync();
    } catch (_err) {
      /* already stopped */
    }
    await Audio.setAudioModeAsync({ allowsRecordingIOS: false });
    tellWeb(webRef, { type: "mic-cancelled" });
  }

  async function stopNativeMic() {
    const recording = recordingRef.current;
    recordingRef.current = null;
    if (!recording) return;
    await recording.stopAndUnloadAsync();
    await Audio.setAudioModeAsync({ allowsRecordingIOS: false });
    const uri = recording.getURI();
    if (!uri) throw new Error("Nothing was recorded. Try again.");
    tellWeb(webRef, { type: "mic-saving" });
    const extra = extraRef.current;
    const clip = new FormData();
    clip.append("file", { uri, name: "clip.m4a", type: "audio/mp4" });
    const heardRes = await fetch(`${APP_URL}/api/transcribe`, {
      method: "POST",
      headers: { "X-Demo-Role": extra.role || "support_worker" },
      body: clip,
    });
    const heardText = await heardRes.text();
    if (!heardRes.ok) throw new Error(apiMessage(heardText, "Could not write what you said."));
    const heard = JSON.parse(heardText);
    const transcript = (heard.transcript || "").trim();
    if (!transcript) throw new Error("Heard nothing. Speak again, then press Stop.");
    tellWeb(webRef, { type: "mic-heard", transcript });
    return;
  }

  async function onWebMessage(event) {
    let message;
    try {
      message = JSON.parse(event.nativeEvent.data);
    } catch (_err) {
      return;
    }
    try {
      if (message.type === "mic-start") await startNativeMic(message);
      if (message.type === "mic-stop") await stopNativeMic();
      if (message.type === "mic-cancel") await cancelNativeMic();
    } catch (err) {
      recordingRef.current = null;
      tellWeb(webRef, {
        type: "mic-error",
        message: apiMessage(err.message, "Microphone failed. Type the log instead."),
      });
    }
  }

  return (
    <View style={styles.screen}>
      <StatusBar style="light" backgroundColor="#005eb8" translucent={false} />
      <View style={{ height: padTop, backgroundColor: "#005eb8" }} />
      {error ? (
        <View style={styles.error}>
          <Text style={styles.title}>Cannot reach Second Shift</Text>
          <Text style={styles.body}>Phone and this computer must be on the same WiFi. The app is at:</Text>
          <Text style={styles.url}>{APP_URL}</Text>
          <Text style={styles.body}>{error}</Text>
          <Pressable style={styles.button} onPress={retry}>
            <Text style={styles.buttonText}>Try again</Text>
          </Pressable>
        </View>
      ) : (
        <WebView
          ref={webRef}
          key={tick}
          source={source}
          style={styles.web}
          startInLoadingState
          renderLoading={() => (
            <View style={styles.loading}>
              <ActivityIndicator size="large" color="#ffffff" />
              <Text style={styles.loadingText}>Opening Second Shift…</Text>
            </View>
          )}
          onError={(event) => setError(event.nativeEvent.description || "Load failed")}
          onHttpError={(event) => {
            if (event.nativeEvent.statusCode >= 400) {
              setError(`HTTP ${event.nativeEvent.statusCode}`);
            }
          }}
          onMessage={onWebMessage}
          injectedJavaScriptBeforeContentLoaded={"window.__SECOND_SHIFT_NATIVE__=true;true;"}
          cacheEnabled={false}
          incognito
          javaScriptEnabled
          domStorageEnabled
          allowsInlineMediaPlayback
          mediaPlaybackRequiresUserAction={false}
          mixedContentMode="always"
          originWhitelist={["*"]}
          setSupportMultipleWindows={false}
          mediaCapturePermissionGrantType="grant"
        />
      )}
      <View style={{ height: padBottom, backgroundColor: "#ffffff" }} />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#005eb8" },
  web: { flex: 1, backgroundColor: "#f0f4f5" },
  loading: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#005eb8",
    gap: 12,
  },
  loadingText: { color: "#ffffff", fontSize: 16, fontWeight: "700" },
  error: { flex: 1, justifyContent: "center", padding: 24, gap: 12, backgroundColor: "#f0f4f5" },
  title: { fontSize: 22, fontWeight: "700", color: "#212b32" },
  body: { fontSize: 16, lineHeight: 22, color: "#4c6272" },
  url: { fontSize: 16, fontWeight: "700", color: "#005eb8" },
  button: { marginTop: 8, backgroundColor: "#007f3b", paddingVertical: 14, borderRadius: 8 },
  buttonText: { color: "#ffffff", textAlign: "center", fontSize: 18, fontWeight: "700" },
});
