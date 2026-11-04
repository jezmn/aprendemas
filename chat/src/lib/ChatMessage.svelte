<script>
    import {
        BrainCircuit,
        User,
        Mic,
        Pause,
        Play,
        RotateCcw,
    } from "lucide-svelte";
    import { marked } from "marked";
    import {
        speech,
        hasEnglishSpeech,
        toggleSpeech,
        restartSpeech,
    } from "./speech.svelte.js";

    let { message, index, userName } = $props();

    let showControls = $derived(
        speech.supported && message.role === "assistant" && hasEnglishSpeech(message),
    );
</script>

<div class={`flex gap-4 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
    <div
        class={`flex w-full max-w-3xl gap-4 ${message.role === "user" ? "flex-row-reverse" : ""}`}
    >
        <div
            class={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border-[3px] border-black shadow-[3px_3px_0_0_#000] ${message.role === "user" ? "bg-slate-800 text-white" : "bg-amber-200 text-black"}`}
        >
            {#if message.role === "user"}
                <User class="h-5 w-5" />
            {:else}
                <BrainCircuit class="h-5 w-5" />
            {/if}
        </div>

        <div
            class={`min-w-0 flex-1 rounded-2xl border-[3px] border-black px-5 py-4 shadow-[4px_4px_0_0_#000] ${message.role === "user" ? "bg-amber-100 text-slate-900" : "bg-white text-slate-900"}`}
        >
            <div class="mb-2 flex flex-wrap items-center justify-between gap-3">
                <div
                    class={`text-xs font-semibold uppercase tracking-[0.22em] ${message.role === "user" ? "text-slate-500" : "text-blue-500"}`}
                >
                    {message.role === "user" ? userName : "AprendeMas"}
                </div>
                {#if showControls}
                    <div class="flex items-center gap-2">
                        <button
                            onclick={() => toggleSpeech(message, index)}
                            disabled={speech.loading && speech.index !== index}
                            class="flex items-center gap-1.5 rounded-lg border-2 border-black bg-sky-200 px-3 py-1.5 text-xs font-bold text-black shadow-[3px_3px_0_0_#000] transition hover:-translate-y-0.5 hover:shadow-[4px_4px_0_0_#000] active:translate-y-0 active:shadow-[2px_2px_0_0_#000] cursor-pointer disabled:opacity-50 disabled:hover:-translate-y-0"
                            aria-label={
                                speech.index === index &&
                                speech.state === "speaking"
                                    ? "Pausar lectura"
                                    : speech.index === index &&
                                          speech.state === "paused"
                                      ? "Reanudar lectura"
                                      : "Leer respuesta"
                            }
                        >
                            {#if speech.index === index && speech.state === "speaking"}
                                <Pause class="h-3.5 w-3.5" />
                                Pausar
                            {:else if speech.index === index && speech.state === "paused"}
                                <Play class="h-3.5 w-3.5" />
                                Reanudar
                            {:else if speech.loading && speech.index === index}
                                <RotateCcw class="h-3.5 w-3.5 animate-spin" />
                                Cargando
                            {:else}
                                <Mic class="h-3.5 w-3.5" />
                                Leer
                            {/if}
                        </button>
                        <button
                            onclick={() => restartSpeech(message, index)}
                            class="flex items-center gap-2 rounded-lg border-2 border-black bg-white px-4 py-2 text-xs font-bold text-slate-700 shadow-[3px_3px_0_0_#000] transition hover:-translate-y-0.5 hover:shadow-[4px_4px_0_0_#000] active:translate-y-0 active:shadow-[2px_2px_0_0_#000] cursor-pointer"
                            aria-label="Reiniciar lectura"
                        >
                            <RotateCcw class="h-4 w-4" />
                            Reiniciar
                        </button>
                    </div>
                {/if}
            </div>
            <div
                class="prose prose-sm max-w-none text-[15px] leading-7 prose-headings:text-slate-900 prose-p:text-slate-700 prose-strong:text-slate-900 prose-li:text-slate-700"
            >
                {@html marked.parse(message.content)}
            </div>
        </div>
    </div>
</div>
