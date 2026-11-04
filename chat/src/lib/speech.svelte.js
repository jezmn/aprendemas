import { marked } from "marked";

// TTS playback state shared with the UI components.
// `state` is one of: "idle" | "speaking" | "paused".
export const speech = $state({
    supported: false,
    loading: false,
    state: "idle",
    index: null,
    text: "",
});

// Non-reactive internals.
let speechRunId = 0;
let audioCtx = null;

export function extractReadableText(content) {
    if (!content) return "";

    if (typeof document === "undefined") {
        return content
            .replace(/[#*_>-]/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    }

    const html = marked.parse(content);
    const container = document.createElement("div");
    container.innerHTML = html;
    return container.textContent?.replace(/\s+/g, " ").trim() || "";
}

export async function checkTtsAvailable() {
    try {
        const res = await fetch("/api/tts/status");
        if (!res.ok) {
            speech.supported = false;
            return;
        }
        const data = await res.json();
        speech.supported = !!data.available;
    } catch {
        speech.supported = false;
    }
}

function clearSpeechState() {
    speech.state = "idle";
    speech.index = null;
    speech.text = "";
}

export function stopSpeech() {
    speechRunId += 1;
    if (audioCtx) {
        try {
            audioCtx.suspend();
        } catch {}
    }
    clearSpeechState();
}

async function ensureAudioCtx() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === "suspended") {
        await audioCtx.resume();
    }
    return audioCtx;
}

async function fetchTts(text, lang) {
    for (let attempt = 0; attempt < 2; attempt++) {
        try {
            const res = await fetch("/api/tts/stream", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: "text=" + encodeURIComponent(text) + "&lang=" + lang,
            });
            if (res.ok) {
                const arrayBuffer = await res.arrayBuffer();
                const sampleRate =
                    Number(res.headers.get("X-Sample-Rate")) || 22050;
                return { arrayBuffer, sampleRate };
            }
        } catch {}
        if (attempt === 0) {
            await new Promise((r) => setTimeout(r, 150));
        }
    }
    return null;
}

async function playBuffer(
    ctx,
    arrayBuffer,
    sampleRate,
    startOffset = 0,
    runId = 0,
) {
    const bytes = new Uint8Array(arrayBuffer);
    const samples = new Int16Array(
        bytes.buffer,
        bytes.byteOffset,
        Math.floor(bytes.length / 2),
    );
    const rate = sampleRate || 22050;
    const totalSamples = samples.length;
    const startSample = Math.floor(startOffset * rate);
    const len = Math.max(0, totalSamples - startSample);
    if (len <= 0) return;
    const buf = ctx.createBuffer(1, len, rate);
    const out = buf.getChannelData(0);
    for (let i = 0; i < len; i++) {
        out[i] = samples[startSample + i] / 32768;
    }

    return new Promise((resolve) => {
        const src = ctx.createBufferSource();
        src.buffer = buf;
        src.connect(ctx.destination);
        let finished = false;
        const done = () => {
            if (finished) return;
            if (speech.state === "paused") {
                setTimeout(done, 100);
                return;
            }
            if (runId !== speechRunId) {
                finished = true;
                resolve();
                return;
            }
            finished = true;
            resolve();
        };
        src.onended = done;
        src.start(0, 0);
        setTimeout(done, (len / rate) * 1000 + 200);
    });
}

function waitWhilePaused(runId) {
    return new Promise((resolve) => {
        const check = () => {
            if (runId !== speechRunId || speech.state !== "paused") {
                resolve();
            } else {
                setTimeout(check, 100);
            }
        };
        check();
    });
}

async function playSegments(
    segments,
    runId,
    segmentIndex = 0,
    segmentOffset = 0,
) {
    if (runId !== speechRunId || segmentIndex >= segments.length) {
        clearSpeechState();
        return;
    }

    if (speech.state === "paused") {
        await waitWhilePaused(runId);
        if (runId !== speechRunId) return;
    }

    const segment = segments[segmentIndex];
    const ctx = await ensureAudioCtx();
    if (runId !== speechRunId) return;

    speech.loading = true;
    const audio = await fetchTts(segment.text, segment.language);
    speech.loading = false;
    if (runId !== speechRunId) return;

    if (!audio) {
        await playSegments(segments, runId, segmentIndex + 1, 0);
        return;
    }

    speech.state = "speaking";
    await playBuffer(
        ctx,
        audio.arrayBuffer,
        audio.sampleRate,
        segmentOffset,
        runId,
    );
    if (runId !== speechRunId) return;

    await waitWhilePaused(runId);
    if (runId !== speechRunId) return;

    if (segmentIndex < segments.length - 1) {
        await new Promise((r) =>
            setTimeout(r, segments[segmentIndex].pauseMs ?? 250),
        );
        await waitWhilePaused(runId);
        if (runId !== speechRunId) return;
    }

    await playSegments(segments, runId, segmentIndex + 1, 0);
}

function speakMessage(message, index) {
    if (!speech.supported || message.role !== "assistant") return;

    const nextText = extractReadableText(message.content);
    if (!nextText) return;

    const segments = buildSpeechSegments(nextText);
    if (!segments.length) return;

    stopSpeech();
    speechRunId += 1;
    const runId = speechRunId;

    speech.index = index;
    speech.text = nextText;
    speech.state = "speaking";

    playSegments(segments, runId);
}

export function toggleSpeech(message, index) {
    if (!speech.supported || message.role !== "assistant") return;

    const messageText = extractReadableText(message.content);
    const isCurrentMessage =
        speech.index === index && speech.text === messageText;

    if (!isCurrentMessage || speech.state === "idle") {
        speakMessage(message, index);
        return;
    }

    if (speech.state === "speaking") {
        if (audioCtx) {
            try {
                audioCtx.suspend();
            } catch {}
        }
        speech.state = "paused";
        return;
    }

    if (speech.state === "paused") {
        if (audioCtx) {
            try {
                audioCtx.resume();
            } catch {}
        }
        speech.state = "speaking";
    }
}

export function restartSpeech(message, index) {
    stopSpeech();
    speakMessage(message, index);
}

// --- Language-aware segment splitting -------------------------------------

const ES_WORDS = new Set(
    "de del al la las los el una uno una para porque pero con como cómo ser estar soy eres es son somos está están estamos nosotros usted tu yo ella ellas ellos verbo verbos ejemplo ejemplos palabra palabras significa estudiante estudiantes amigo amigos inglés aprender buenas hola claro escuela quiero quieres quiere practica practicar cuando dónde aquí algo su les".split(
        /\s+/,
    ),
);

const EN_WORDS = new Set(
    "the this that these those how what who when where why is are am was were be been being have has had do does did and or with for from not to into on in at by of as it they we you he she his her their our its student teacher friends happy brothers today".split(
        /\s+/,
    ),
);

function detectSegmentLanguage(text) {
    const t = (text || "").toLowerCase();
    if (/[ñ¡¿áéíóúü]/.test(t)) return "es";
    const words = t.match(/[a-záéíóúüñ]+/g) || [];
    const esHits = words.filter((w) => ES_WORDS.has(w)).length;
    const enHits = words.filter((w) => EN_WORDS.has(w)).length;
    return esHits > enHits ? "es" : "en";
}

function createSpeechSegment(text, language, options = {}) {
    const clean = (text || "").replace(/\s+/g, " ").trim();
    if (!clean) return null;
    return {
        text: clean,
        language: language || "en",
        pauseMs: options.pauseMs ?? 220,
        keepSeparate: !!(options && options.keepSeparate),
    };
}

function splitVocabularyList(text) {
    const vocabularyPattern = /([a-z][a-z\s'-]*)(?:\s*\(([^)]+)\))?/gi;
    const segments = [];
    let match;

    while ((match = vocabularyPattern.exec(text)) !== null) {
        const englishTerm = createSpeechSegment(match[1], "en", {
            pauseMs: match[2] ? 120 : 220,
            keepSeparate: true,
        });
        if (englishTerm) segments.push(englishTerm);

        if (match[2]) {
            const translatedTerm = createSpeechSegment(match[2], "es", {
                pauseMs: 260,
                keepSeparate: true,
            });
            if (translatedTerm) segments.push(translatedTerm);
        }
    }

    return segments;
}

function splitMixedLanguageChunk(text) {
    const trimmedText = text.trim();
    if (!trimmedText) return [];

    // Vocabulary lines like "I am = Yo soy": only the English side is spoken.
    const eqIndex = trimmedText.indexOf("=");
    if (eqIndex > 0) {
        const left = trimmedText.slice(0, eqIndex).trim();
        const right = trimmedText.slice(eqIndex + 1).trim();
        if (left && right) {
            const leftSegment = createSpeechSegment(
                left,
                detectSegmentLanguage(left),
            );
            if (leftSegment) return [leftSegment];
        }
    }

    const colonIndex = trimmedText.indexOf(":");
    if (colonIndex >= 0) {
        const prefix = trimmedText.slice(0, colonIndex + 1).trim();
        const suffix = trimmedText.slice(colonIndex + 1).trim();

        if (/\bin english\b/i.test(prefix) && suffix) {
            const segments = [];
            const prefixSegment = createSpeechSegment(
                prefix,
                detectSegmentLanguage(prefix),
            );
            if (prefixSegment) segments.push(prefixSegment);

            const vocabularySegments = splitVocabularyList(suffix);
            if (vocabularySegments.length) {
                return [...segments, ...vocabularySegments];
            }
        }
    }

    const parts = trimmedText.split(/(\([^()]+\))/g).filter(Boolean);
    const segments = [];

    for (const part of parts) {
        const trimmedPart = part.trim();
        if (!trimmedPart) continue;

        const chunkText =
            trimmedPart.startsWith("(") && trimmedPart.endsWith(")")
                ? trimmedPart.slice(1, -1)
                : trimmedPart;

        const language = detectSegmentLanguage(chunkText);
        const segment = createSpeechSegment(chunkText, language);
        if (segment) segments.push(segment);
    }

    return segments;
}

function mergeAdjacentSegments(segments) {
    const merged = [];

    for (const segment of segments) {
        const previous = merged[merged.length - 1];
        if (
            previous &&
            previous.language === segment.language &&
            !previous.keepSeparate &&
            !segment.keepSeparate
        ) {
            previous.text = (previous.text + " " + segment.text)
                .replace(/\s+/g, " ")
                .trim();
        } else {
            merged.push({ ...segment });
        }
    }

    return merged;
}

function buildSpeechSegments(text) {
    const normalizedText = text.replace(/\s+/g, " ").trim();
    if (!normalizedText) return [];

    const phraseParts = normalizedText
        .split(/(?<=[.!?,;])\s+/)
        .map((part) => part.trim())
        .filter(Boolean);

    const segments = [];

    for (const phrasePart of phraseParts) {
        const chunkSegments = splitMixedLanguageChunk(phrasePart);
        const endPauseMs = /[,;]$/.test(phrasePart) ? 250 : 420;
        for (let i = 0; i < chunkSegments.length; i++) {
            // Keep clauses apart so the pause between them survives the merge.
            chunkSegments[i].keepSeparate = true;
            if (i === chunkSegments.length - 1)
                chunkSegments[i].pauseMs = endPauseMs;
            segments.push(chunkSegments[i]);
        }
    }

    // A single English voice reads every segment, no matter its language.
    return mergeAdjacentSegments(segments).map((segment) => ({
        ...segment,
        language: "en",
    }));
}

export function hasEnglishSpeech(message) {
    const text = extractReadableText(message?.content);
    if (!text) return false;
    return buildSpeechSegments(text).some((segment) => segment.language === "en");
}
