<script>
import { onMount } from "svelte";
import { PanelLeft, Sparkles, Trash2, MessageSquare } from "lucide-svelte";

    let {
        sessions = [],
        sessionId = null,
        sidebarOpen = $bindable(false),
        sidebarCollapsed = $bindable(false),
        sidebarWidth = $bindable(320),
        onnewchat,
        onselect,
        ondelete,
    } = $props();

    let resizing = $state(false);

    function startResize(e) {
        if (e.button !== undefined && e.button !== 0) return;
        resizing = true;
        // One toggle per gesture; afterward it becomes a pure resize.
        let base = e.clientX;
        let toggled = false;
        const onMove = (ev) => {
            const w = ev.clientX;
            if (sidebarCollapsed) {
                if (!toggled && w - base > 40) {
                    toggled = true;
                    sidebarCollapsed = false;
                    localStorage.setItem("AprendeMas_sidebar_collapsed", "false");
                    base = w;
                    sidebarWidth = Math.min(520, Math.max(280, w));
                }
                return;
            }
            // Collapse threshold stays below min width to avoid jitter.
            if (!toggled && w < 240) {
                toggled = true;
                sidebarCollapsed = true;
                localStorage.setItem("AprendeMas_sidebar_collapsed", "true");
                return;
            }
            sidebarWidth = Math.min(520, Math.max(280, w));
        };
        const onUp = () => {
            resizing = false;
            window.removeEventListener("pointermove", onMove);
            window.removeEventListener("pointerup", onUp);
            window.removeEventListener("pointercancel", onUp);
        };
        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", onUp);
        window.addEventListener("pointercancel", onUp);
        e.preventDefault();
    }

    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString("es", {
            month: "short",
            day: "numeric",
        });
    }

    function getInitial(str) {
        return str ? str.charAt(0).toUpperCase() : "A";
    }

    let appVersion = $state("1.1.0");

    onMount(() => {
        fetch("/api/version")
            .then((r) => r.json())
            .then((data) => {
                if (data?.version) appVersion = data.version;
            })
            .catch(() => {});
    });
</script>

<div
    class={`fixed inset-0 z-40 bg-slate-950/30  transition-opacity duration-300 lg:hidden ${sidebarOpen ? "opacity-100" : "pointer-events-none opacity-0"}`}
    role="button"
    tabindex="0"
    onkeydown={(e) => {
        if (e.key === "Enter" || e.key === " " || e.key === "Escape")
            sidebarOpen = false;
    }}
    onclick={() => (sidebarOpen = false)}
></div>

<aside
    class={`fixed inset-y-0 left-0 z-50 max-w-[92vw] flex flex-col bg-amber-50 border-r-[3px] border-black ${resizing ? "transition-none" : "transition-[width,transform] duration-300"} lg:max-w-none lg:relative lg:z-0 lg:translate-x-0 ${sidebarCollapsed ? "lg:w-18" : ""} ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}
    style={sidebarCollapsed ? "" : `width: ${sidebarWidth}px`}
>
    <div
        class={`flex pb-2 pt-5 ${sidebarCollapsed ? "justify-center px-2" : "items-center justify-between px-5"}`}
    >
        {#if !sidebarCollapsed}
            <img
                src="/logo.png"
                alt="AprendeMas"
                class="h-22 w-auto object-contain"
            />
        {/if}
        <button
            onclick={() => {
                sidebarCollapsed = !sidebarCollapsed;
                localStorage.setItem(
                    "AprendeMas_sidebar_collapsed",
                    String(sidebarCollapsed),
                );
            }}
            class="max-lg:hidden rounded-xl border-[3px] border-black bg-amber-200 p-2.5 text-black shadow-[3px_3px_0_0_#000] transition-all hover:-translate-y-0.5 hover:shadow-[4px_4px_0_0_#000] cursor-pointer"
            aria-label={sidebarCollapsed ? "Expandir sidebar" : "Colapsar sidebar"}
            title={sidebarCollapsed ? "Expandir" : "Colapsar"}
        >
            <PanelLeft
                class={`h-5 w-5 transition-transform duration-300 ${sidebarCollapsed ? "rotate-180" : ""}`}
            />
        </button>
    </div>
    <div
        class={`border-b border-blue-100/80 pb-5 pt-4 ${sidebarCollapsed ? "px-3" : "px-5"}`}
    >
        <button
            onclick={onnewchat}
            class={`flex w-full items-center justify-center rounded-xl border-[3px] border-black bg-sky-300 py-3 font-bold text-black shadow-[4px_4px_0_0_#000] transition-all hover:-translate-y-0.5 hover:shadow-[5px_5px_0_0_#000] active:translate-y-0 active:shadow-[2px_2px_0_0_#000] cursor-pointer ${sidebarCollapsed ? "px-0" : "gap-2 px-4"}`}
            aria-label="Nuevo chat"
        >
            <Sparkles class="h-4 w-4" />
            {#if !sidebarCollapsed}
                Nuevo chat
            {/if}
        </button>
    </div>

    <div
        class={`min-h-0 flex-1 pb-4 pt-3 ${sidebarCollapsed ? "px-2" : "px-4"}`}
    >
        {#if !sidebarCollapsed}
            <div class="mb-3 flex items-center justify-between px-1">
                <div
                    class="text-xs font-bold uppercase tracking-[0.22em] text-slate-500"
                >
                    Recientes
                </div>
                <div class="text-[11px] font-medium text-slate-400 select-none">
                    v{appVersion}
                </div>
            </div>
        {/if}

        <div class="scrollbar-thin h-full space-y-2 overflow-y-auto pr-1">
            {#each sessions as session}
                <div class="group relative">
                    <button
                        onclick={() => {
                            onselect(session.session_id);
                            sidebarOpen = false;
                        }}
                        class={`w-full rounded-xl border-2 border-black text-left transition-all cursor-pointer shadow-[3px_3px_0_0_#000] ${sidebarCollapsed ? "p-2.5" : "p-3.5 pr-10"} ${sessionId === session.session_id ? "bg-amber-200" : "bg-white hover:bg-amber-100"}`}
                        aria-label={session.title || "Chat"}
                    >
                        <div
                            class={`flex min-w-0 items-center ${sidebarCollapsed ? "justify-center" : "gap-3"}`}
                        >
                            <div
                                class={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border-2 border-black text-sm font-black ${sessionId === session.session_id ? "bg-amber-300 text-black" : "bg-sky-200 text-black"}`}
                            >
                                {getInitial(session.title || "C")}
                            </div>
                            {#if !sidebarCollapsed}
                                <div class="min-w-0">
                                    <div
                                        class="truncate text-sm font-bold text-slate-800"
                                    >
                                        {session.title || "Chat"}
                                    </div>
                                    <div class="mt-0.5 text-xs text-slate-500">
                                        {session.message_count} mensajes
                                    </div>
                                </div>
                            {/if}
                        </div>
                        {#if !sidebarCollapsed}
                            <div class="mt-2 text-xs text-slate-500">
                                {formatDate(session.last_activity)}
                            </div>
                        {/if}
                    </button>
                    {#if !sidebarCollapsed}
                        <button
                            onclick={(e) => ondelete(session.session_id, e)}
                            class="absolute right-3 top-3 rounded-lg border-2 border-transparent p-1.5 text-slate-600 opacity-0 transition-all hover:border-black hover:bg-white hover:text-black hover:shadow-[2px_2px_0_0_#000] group-hover:opacity-100 cursor-pointer"
                            aria-label="Eliminar chat"
                        >
                            <Trash2 class="h-4 w-4" />
                        </button>
                    {/if}
                </div>
            {/each}

            {#if sessions.length === 0}
                <div
                    class={`rounded-2xl border-[3px] border-black bg-white text-center text-sm font-bold text-slate-600 shadow-[3px_3px_0_0_#000] ${sidebarCollapsed ? "p-3" : "p-5"}`}
                >
                    {#if sidebarCollapsed}
                        <MessageSquare class="mx-auto h-5 w-5 text-blue-400" />
                    {:else}
                        Tus conversaciones aparecerán aquí cuando empieces a
                        practicar.
                    {/if}
                </div>
            {/if}
        </div>
    </div>
    <div
        class="absolute right-0 top-0 z-10 h-full w-2 cursor-col-resize touch-none"
        onpointerdown={startResize}
        role="separator"
        aria-orientation="vertical"
        aria-label="Arrastra para ajustar el ancho"
    ></div>
</aside>

<style>
    /* Thin scrollbar that only appears on hover. */
    .scrollbar-thin {
        scrollbar-width: thin;
        scrollbar-color: transparent transparent;
    }

    .scrollbar-thin:hover {
        scrollbar-color: #cbd5e1 transparent;
    }

    .scrollbar-thin::-webkit-scrollbar {
        width: 6px;
    }

    .scrollbar-thin::-webkit-scrollbar-track {
        background: transparent;
    }

    .scrollbar-thin::-webkit-scrollbar-thumb {
        background: transparent;
        border-radius: 999px;
    }

    .scrollbar-thin:hover::-webkit-scrollbar-thumb {
        background: #cbd5e1;
    }

    .scrollbar-thin::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
</style>
