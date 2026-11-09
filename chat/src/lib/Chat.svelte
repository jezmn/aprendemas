<script>
    import { onMount, onDestroy } from "svelte";
    import { BrainCircuit, PanelLeft, Smile } from "lucide-svelte";
    import ChatSidebar from "./ChatSidebar.svelte";
    import ChatMessage from "./ChatMessage.svelte";
    import MessageComposer from "./MessageComposer.svelte";
    import { checkTtsAvailable, stopSpeech } from "./speech.svelte.js";

    let messages = $state([]);
    let inputMessage = $state("");
    let isLoading = $state(false);
    let suggestions = $state([]);
    let hasWarmedUp = $state(false);
    let showWakePopup = $state(false);
    let sessionId = $state(null);
    let sessionTitle = $state("");
    /** @type {HTMLDivElement | null} */
    let messagesContainer = $state(null);
    let sessions = $state([]);
    let sidebarOpen = $state(false);
    let sidebarCollapsed = $state(false);
    let sidebarWidth = $state(320);
    let userName = $state("usuario");
    let editingName = $state(false);
    let tempName = $state("");
    let messageQueue = $state([]);
    let abortController = $state(null);
    const API_URL = "/api";

    // Rotating suggestion bank for kids (A1-A2). 3 shown per message.
    const SUGGESTION_BANK = [
        "Cuéntame un cuento corto",
        "Enséñame 5 nombres de animales",
        "Cuenta conmigo del 1 al 10",
        "Enséñame los colores en inglés",
        "¿Cómo digo 'me gusta' en inglés?",
        "Practica: I am / You are / He is",
        "Hazme un mini examen",
        "Enséñame palabras de la escuela",
        "Enséñame 5 palabras de comida",
        "Vocabulario de la familia en inglés",
        "Los días de la semana en inglés",
        "¿Cómo me presento en inglés?",
        "Enséñame los números hasta el 20",
        "Vocabulario de mascotas en inglés",
        "Partes del cuerpo en inglés",
        "Enséñame 5 palabras de frutas",
        "Palabras del clima en inglés",
        "Vocabulario de ropa en inglés",
        "Enséñame 5 verbos con ejemplos",
        "¿Cómo digo 'tengo hambre' en inglés?",
        "Cuéntame un cuento sobre un perro",
        "Colores: red, blue, green... y más",
        "Practica: this / that / these / those",
        "¿Cómo digo 'mi cumpleaños' en inglés?",
        "Cosas del salón de clases en inglés",
        "Enséñame 5 profesiones (teacher, doctor...)",
        "¿Cómo digo 'gracias' y 'de nada' en inglés?",
        "Cuéntame un cuento sobre el espacio",
        "Practica: have / has",
        "Deportes y juegos en inglés",
        "¿Cómo digo 'qué hora es' en inglés?",
        "Emociones en inglés: happy, sad, angry...",
        "Enséñame los meses del año",
        "Practica: there is / there are",
        "¿Cómo digo 'vivo en' en inglés?",
        "Cuéntame un cuento sobre el océano",
        "Animales del zoológico en inglés",
        "¿Cómo digo 'por favor' y 'lo siento' en inglés?",
        "Comida del desayuno en inglés",
        "Practica: can / can't",
        "Dame 5 preguntas para hacerle a mis amigos",
        "Sobre la escuela: enséñame más palabras de la escuela",
        "Cuéntame un cuento corto y gracioso",
        "Practica: go / goes",
        "Enséñame 5 cuartos de la casa",
        "¿Cómo digo 'me llamo' en inglés?",
        "Transporte: car, bus, train...",
        "Practica: want / wants",
        "Enséñame 5 palabras de la naturaleza",
        "Hazme un examen de ortografía",
        "¿Cómo digo 'quiero jugar' en inglés?",
        "Animales de la granja en inglés",
        "Practica: do / does",
        "Enséñame 5 palabras de juguetes",
        "Cuéntame un cuento sobre un árbol mágico",
        "¿Cómo digo 'hasta luego' en inglés?",
        "Animales del mar en inglés",
        "Practica: like / likes",
        "Dame un trabalenguas en inglés",
        "Enséñame 5 frases para ordenar comida",
        "¿Cómo digo 'mi amigo es alto' en inglés?",
        "El clima: what's the weather like today?",
        "Practica: preguntas con to be (Are you...?)",
        "Enséñame una palabra nueva cada día",
        "Practica los números: del 21 al 50",
    ];
    let suggestionOffset = 0;

    function nextSuggestions() {
        const n = SUGGESTION_BANK.length;
        const count = window.innerWidth < 640 ? 2 : 3;
        const picked = [];
        for (let i = 0; i < count; i++) {
            picked.push(SUGGESTION_BANK[(suggestionOffset + i) % n]);
        }
        suggestionOffset = (suggestionOffset + count) % n;
        return picked;
    }

    const GAMES = {
        colors: {
            title: "Colores",
            prompt: "Enséñame los colores en inglés con ejemplos.",
            image: "/images/colors.png",
        },
        animals: {
            title: "Animales",
            prompt: "Enséñame los nombres de animales en inglés.",
            image: "/images/animals.png",
        },
        numbers: {
            title: "Números",
            prompt: "Enséñame los números en inglés.",
            image: "/images/numbers.png",
        },
        story: {
            title: "Cuentos",
            prompt: "Cuéntame un cuento corto en inglés.",
            image: "/images/stories.png",
        },
    };

    onMount(() => {
        const savedName = localStorage.getItem("AprendeMas_username");
        if (savedName) userName = savedName;
        sidebarCollapsed =
            localStorage.getItem("AprendeMas_sidebar_collapsed") === "true";
        checkTtsAvailable();
        loadSessions();
    });

    onDestroy(() => {
        stopSpeech();
    });

    async function loadSessions() {
        try {
            const res = await fetch(`${API_URL}/sessions`);
            sessions = await res.json();
        } catch {}
    }

    async function loadHistory(id) {
        try {
            stopSpeech();
            const res = await fetch(`${API_URL}/sessions/${id}/history`);
            const data = await res.json();
            sessionId = id;
            messages = data.history
                .map((h) => [
                    { role: "user", content: h.user },
                    { role: "assistant", content: h.assistant },
                ])
                .flat();
            sessionTitle =
                sessions.find((s) => s.session_id === id)?.title || "Chat";
            scrollToBottom();
        } catch {}
    }

    async function deleteSession(id, e) {
        e.stopPropagation();
        try {
            if (sessionId === id) stopSpeech();
            await fetch(`${API_URL}/sessions/${id}`, { method: "DELETE" });
            if (sessionId === id) {
                messages = [];
                sessionId = null;
                sessionTitle = "";
            }
            loadSessions();
        } catch {}
    }

    function startNewChat() {
        stopSpeech();
        messages = [];
        sessionId = null;
        sessionTitle = "";
        sidebarOpen = false;
        suggestions = [];
    }

    function toggleSidebar() {
        sidebarOpen = !sidebarOpen;
        // On mobile the drawer is always full: collapsed mode is desktop-only.
        if (sidebarOpen && typeof window !== "undefined" && window.innerWidth < 1024 && sidebarCollapsed) {
            sidebarCollapsed = false;
            localStorage.setItem("AprendeMas_sidebar_collapsed", "false");
        }
    }

    function startEditName() {
        tempName = userName;
        editingName = true;
    }

    function saveName() {
        if (tempName.trim()) {
            userName = tempName.trim();
            localStorage.setItem("AprendeMas_username", userName);
        }
        editingName = false;
    }

    function handleNameKeydown(e) {
        if (e.key === "Enter") saveName();
        if (e.key === "Escape") editingName = false;
    }

    function startGame(gameKey) {
        const game = GAMES[gameKey];
        if (game) {
            inputMessage = game.prompt;
            sendMessage();
        }
    }

    async function sendMessage() {
        if (!inputMessage.trim()) return;
        if (isLoading) {
            messageQueue = [...messageQueue, inputMessage.trim()];
            inputMessage = "";
            return;
        }
        stopSpeech();

        const userMessage = inputMessage.trim();
        inputMessage = "";

        messages = [...messages, { role: "user", content: userMessage }];
        scrollToBottom();
        isLoading = true;
        if (!hasWarmedUp) showWakePopup = true;

        const controller = new AbortController();
        abortController = controller;
        let abortedByUser = false;
        try {
            const response = await fetch(`${API_URL}/chat/stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userMessage,
                    session_id: sessionId,
                }),
                signal: controller.signal,
            });

            if (!response.body) {
                throw new Error("no body");
            }
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let fullContent = "";
            let started = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.token) {
                                fullContent += data.token;
                                if (!started) {
                                    started = true;
                                    showWakePopup = false;
                                    messages = [
                                        ...messages,
                                        {
                                            role: "assistant",
                                            content: fullContent,
                                        },
                                    ];
                                } else {
                                    messages[messages.length - 1] = {
                                        ...messages[messages.length - 1],
                                        content: fullContent,
                                    };
                                }
                            }
                            if (data.session_id) sessionId = data.session_id;
                            if (data.title) sessionTitle = data.title;
                        } catch {}
                    }
                }
                scrollToBottom();
            }

            loadSessions();
        } catch (err) {
            if (err.name === "AbortError") {
                abortedByUser = true;
                if (fullContent) {
                    messages = [
                        ...messages,
                        { role: "assistant", content: fullContent },
                    ];
                }
            } else {
                messages = [
                    ...messages,
                    {
                        role: "assistant",
                        content: "¡Ups! Algo salió mal. Inténtalo de nuevo.",
                    },
                ];
            }
        } finally {
            isLoading = false;
            hasWarmedUp = true;
            showWakePopup = false;
            suggestions = nextSuggestions();
            if (abortController === controller) abortController = null;
            scrollToBottom();
            if (!abortedByUser && messageQueue.length > 0) {
                const next = messageQueue[0];
                messageQueue = messageQueue.slice(1);
                inputMessage = next;
                sendMessage();
            }
        }
    }

    function stopGeneration() {
        if (abortController) {
            abortController.abort();
        }
        isLoading = false;
        messageQueue = [];
    }

    function scrollToBottom() {
        if (messagesContainer) {
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 10);
        }
    }
</script>

<div
    class="flex h-dvh overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.18),transparent_32%),radial-gradient(circle_at_top_right,rgba(59,130,246,0.12),transparent_28%),linear-gradient(180deg,#fbfdff_0%,#f2f8ff_42%,#eef6ff_100%)] text-slate-800"
>
    <ChatSidebar
        {sessions}
        {sessionId}
        bind:sidebarOpen
        bind:sidebarCollapsed
        bind:sidebarWidth
        onnewchat={startNewChat}
        onselect={loadHistory}
        ondelete={deleteSession}
    />

    <main class="flex min-w-0 flex-1 flex-col">
        <header
            class="border-b-[3px] border-black bg-amber-50 px-3 py-3 md:px-6 md:py-4"
        >
            <div class="flex w-full items-center justify-between gap-4">
                <div class="flex min-w-0 items-center gap-3">
                    <button
                        onclick={toggleSidebar}
                        class="rounded-xl border-[3px] border-black bg-amber-200 p-2.5 text-black shadow-[3px_3px_0_0_#000] transition-all hover:-translate-y-0.5 hover:shadow-[4px_4px_0_0_#000] active:translate-y-0 active:shadow-[2px_2px_0_0_#000] cursor-pointer lg:hidden"
                        aria-label="Abrir sidebar"
                    >
                        <PanelLeft class="h-5 w-5" />
                    </button>

                    <div class="min-w-0">
                        <div
                            class="truncate rounded-xl border-2 border-black bg-amber-200 px-3 py-1 text-base font-bold tracking-tight text-black shadow-[2px_2px_0_0_#000] md:text-lg"
                        >
                            {sessionTitle || "Nueva conversación"}
                        </div>
                    </div>
                </div>

                <div class="flex items-center gap-3">
                    {#if editingName}
                        <input
                            type="text"
                            bind:value={tempName}
                            onkeydown={handleNameKeydown}
                            onblur={saveName}
                            class="w-36 rounded-xl border-[3px] border-black bg-white px-3 py-2 text-base md:text-sm font-bold text-slate-900 outline-none shadow-[3px_3px_0_0_#000] focus:bg-amber-100 focus:shadow-[4px_4px_0_0_#000] transition-all"
                            placeholder="Tu nombre"
                        />
                    {:else}
                        <button
                            onclick={startEditName}
                            class="flex items-center gap-3 rounded-xl border-[3px] border-black bg-amber-200 px-3 py-2 shadow-[3px_3px_0_0_#000] transition-all hover:-translate-y-0.5 hover:shadow-[4px_4px_0_0_#000] cursor-pointer"
                        >
                            <div
                                class="flex h-9 w-9 items-center justify-center rounded-lg border-2 border-black bg-sky-200 text-black"
                            >
                                <Smile class="h-5 w-5" />
                            </div>
                            <div class="hidden text-left sm:block">
                                <div
                                    class="text-xs uppercase tracking-[0.18em] text-slate-500"
                                >
                                    Perfil
                                </div>
                                <div class="text-sm font-bold text-slate-800">
                                    {userName}
                                </div>
                            </div>
                        </button>
                    {/if}
                </div>
            </div>
        </header>

        <div
            class="min-h-0 flex-1 overflow-y-auto px-3 py-5 md:px-6 md:py-8"
            bind:this={messagesContainer}
            aria-live="polite"
            aria-atomic="false"
        >
            <div class="mx-auto flex min-h-full w-full max-w-5xl flex-col">
                {#if messages.length === 0}
                    <section
                        class="flex flex-1 items-center justify-center py-6"
                    >
                        <div
                            class="w-full max-w-4xl rounded-3xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000] md:p-8"
                        >
                            <div class="mx-auto max-w-3xl text-center">
                                <h1
                                    class="text-3xl font-black leading-tight tracking-tight text-slate-900 md:text-5xl"
                                >
                                    Hola, {userName}
                                </h1>
                                <p
                                    class="mt-4 text-base leading-7 text-slate-600"
                                >
                                    Elige un tema o escribe tu pregunta para
                                    empezar.
                                </p>

                                <div
                                    class="mt-8 grid grid-cols-2 gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-4"
                                >
                                    {#each Object.entries(GAMES) as [key, { title, image }]}
                                        <button
                                            onclick={() => startGame(key)}
                                            class="group rounded-2xl border-[3px] border-black bg-amber-200 p-4 text-center shadow-[5px_5px_0_0_#000] transition-all hover:-translate-y-1 hover:shadow-[7px_7px_0_0_#000] active:translate-y-0 active:shadow-[3px_3px_0_0_#000] cursor-pointer"
                                        >
                                            <img
                                                src={image}
                                                alt={title}
                                                class="mb-3 mx-auto h-16 w-16 object-contain transition-transform group-hover:scale-110 md:h-20 md:w-20"
                                                draggable="false"
                                            />
                                            <div
                                                class="text-lg font-black text-black"
                                            >
                                                {title}
                                            </div>
                                        </button>
                                    {/each}
                                </div>
                            </div>
                        </div>
                    </section>
                {/if}

                {#if messages.length > 0}
                    <section
                        class="space-y-6 py-3 md:py-2 sm:space-y-5"
                    >
                    {#each messages as message, index}
                            {#if message.role !== "system"}
                                <ChatMessage
                                    {message}
                                    {index}
                                    {userName}
                                />
                            {/if}
                        {/each}

                        {#if isLoading && messages[messages.length - 1].role === "user"}
                            <div class="flex justify-start">
                                <div class="flex w-full max-w-3xl gap-4">
                                    <div
                                        class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border-[3px] border-black bg-amber-200 text-black shadow-[3px_3px_0_0_#000]"
                                    >
                                        <BrainCircuit class="h-5 w-5" />
                                    </div>
                                    <div
                                        class="rounded-2xl border-[3px] border-black bg-white px-5 py-4 shadow-[4px_4px_0_0_#000]"
                                    >
                                        <div
                                            class="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-blue-500"
                                        >
                                            AprendeMas
                                        </div>
                                        <div class="flex gap-1.5">
                                            <span
                                                class="h-2 w-2 rounded-full bg-blue-400 animate-bounce"
                                            ></span>
                                            <span
                                                class="h-2 w-2 rounded-full bg-blue-400 animate-bounce"
                                                style="animation-delay: 0.15s"
                                            ></span>
                                            <span
                                                class="h-2 w-2 rounded-full bg-blue-400 animate-bounce"
                                                style="animation-delay: 0.3s"
                                            ></span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        {/if}
                    </section>
                {/if}
            </div>
        </div>

        <MessageComposer
            bind:inputMessage
            {isLoading}
            {suggestions}
            onsend={sendMessage}
            onstop={stopGeneration}
        />
    </main>

    {#if showWakePopup}
        <div
            class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm"
        >
            <div
                class="mx-4 w-full max-w-sm rounded-2xl border-[3px] border-black bg-amber-100 p-6 text-center shadow-[6px_6px_0_0_#000]"
            >
                <div class="mb-3 text-4xl animate-pulse">💤</div>
                <div class="text-lg font-black text-slate-900">
                    AprendeMas se está despertando...
                </div>
                <div class="mt-2 text-sm text-slate-600">
                    Espera unos segundos mientras carga el modelo.
                </div>
            </div>
        </div>
    {/if}
</div>
