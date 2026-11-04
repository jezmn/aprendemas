<script>
    import { onMount } from "svelte";
    import { Send, Square } from "lucide-svelte";

    let {
        inputMessage = $bindable(""),
        isLoading = false,
        suggestions = [],
        onsend,
        onstop,
    } = $props();

    // Placeholder más corto en teléfono para que entre entero en pantallas angostas.
    let isPhone = $state(false);

    onMount(() => {
        const mq = window.matchMedia("(max-width: 767px)");
        const apply = () => (isPhone = mq.matches);
        apply();
        mq.addEventListener("change", apply);
        return () => mq.removeEventListener("change", apply);
    });

    function handleKeydown(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onsend();
        }
    }
</script>

<div class="bg-transparent px-4 py-4 md:px-6 md:py-10">
    <div class="mx-auto w-full max-w-4xl">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
            {#if isLoading}
                <div class="text-sm font-semibold text-slate-600">
                    AprendeMas está escribiendo...
                </div>
            {/if}
            <div class="flex flex-wrap items-center gap-2">
                {#if isLoading}
                    <button
                        onclick={onstop}
                        class="flex items-center gap-2 rounded-lg border-2 border-black bg-red-200 px-3 py-1.5 text-xs font-bold text-black shadow-[2px_2px_0_0_#000] transition-all hover:-translate-y-0.5 hover:shadow-[3px_3px_0_0_#000] active:translate-y-0 active:shadow-[1px_1px_0_0_#000] cursor-pointer"
                        aria-label="Detener generación"
                    >
                        <Square class="h-3.5 w-3.5" />
                        Detener
                    </button>
                {/if}
            </div>
        </div>
        {#if suggestions.length && !isLoading}
            <div class="mb-3 flex flex-wrap gap-2">
                {#each suggestions as sug}
                    <button
                        onclick={() => {
                            inputMessage = sug;
                            onsend();
                        }}
                        class="rounded-lg border-2 border-black bg-sky-200 px-3 py-2 text-xs font-bold text-black shadow-[3px_3px_0_0_#000] transition hover:-translate-y-0.5 hover:shadow-[4px_4px_0_0_#000] active:translate-y-0 active:shadow-[2px_2px_0_0_#000] cursor-pointer"
                    >
                        {sug}
                    </button>
                {/each}
            </div>
        {/if}
        <div class="flex items-end gap-3">
            <textarea
                bind:value={inputMessage}
                placeholder={
                    isPhone
                        ? "Pregunta cualquier cosa"
                        : "Pregunta cualquier cosa para aprender inglés"
                }
                onkeydown={handleKeydown}
                rows="1"
                class="min-h-14 flex-1 resize-none rounded-2xl border-[3px] border-black bg-white px-5 py-4 text-base md:text-[15px] text-slate-900 outline-none transition placeholder:text-slate-500 focus:shadow-[4px_4px_0_0_#000]"
            ></textarea>

            {#if !isLoading}
                <button
                    onclick={onsend}
                    disabled={!inputMessage.trim()}
                    class="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border-[3px] border-black bg-amber-300 text-black shadow-[4px_4px_0_0_#000] transition-all hover:-translate-y-0.5 hover:shadow-[5px_5px_0_0_#000] active:translate-y-0 active:shadow-[2px_2px_0_0_#000] disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
                    aria-label="Enviar"
                >
                    <Send class="h-5 w-5" />
                </button>
            {/if}
        </div>
    </div>
</div>
