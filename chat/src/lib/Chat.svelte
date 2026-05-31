<script>
  import { onMount } from 'svelte';
  import { marked } from 'marked';
  import {
    Brain, BrainCircuit, Sparkles, Trash2, Smile, User,
    Palette, Dog, Calculator, BookOpen,
    Send, PanelLeft
  } from 'lucide-svelte';

  let messages = $state([]);
  let inputMessage = $state('');
  let isLoading = $state(false);
  let sessionId = $state(null);
  let sessionTitle = $state('');
  let messagesContainer = $state(null);
  let sessions = $state([]);
  let sidebarOpen = $state(false);
  let userName = $state('usuario');
  let editingName = $state(false);
  let tempName = $state('');
  let currentGame = $state(null);
  let gameQuestion = $state('');
  let gameOptions = $state([]);
  let gameAnswer = $state('');
  const API_URL = '/api';

  const GAMES = {
    colors: {
      title: 'Colores',
      prompt: 'Enséñame los colores en inglés con ejemplos.',
      icon: Palette
    },
    animals: {
      title: 'Animales',
      prompt: 'Enséñame los nombres de animales en inglés.',
      icon: Dog
    },
    numbers: {
      title: 'Números',
      prompt: 'Enséñame los números en inglés.',
      icon: Calculator
    },
    story: {
      title: 'Cuentos',
      prompt: 'Cuéntame un cuento corto en inglés.',
      icon: BookOpen
    }
  };

  onMount(() => {
    const savedName = localStorage.getItem('leximind_username');
    if (savedName) userName = savedName;
    loadSessions();
  });

  async function loadSessions() {
    try {
      const res = await fetch(`${API_URL}/sessions`);
      sessions = await res.json();
    } catch {}
  }

  async function loadHistory(id) {
    try {
      const res = await fetch(`${API_URL}/sessions/${id}/history`);
      const data = await res.json();
      sessionId = id;
      messages = data.history.map(h => [
        { role: 'user', content: h.user },
        { role: 'assistant', content: h.assistant }
      ]).flat();
      sessionTitle = sessions.find(s => s.session_id === id)?.title || 'Chat';
      scrollToBottom();
    } catch {}
  }

  async function deleteSession(id, e) {
    e.stopPropagation();
    try {
      await fetch(`${API_URL}/sessions/${id}`, { method: 'DELETE' });
      if (sessionId === id) {
        messages = [];
        sessionId = null;
        sessionTitle = '';
      }
      loadSessions();
    } catch {}
  }

  function startNewChat() {
    messages = [];
    sessionId = null;
    sessionTitle = '';
    currentGame = null;
    sidebarOpen = false;
  }

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }

  function startEditName() {
    tempName = userName;
    editingName = true;
  }

  function saveName() {
    if (tempName.trim()) {
      userName = tempName.trim();
      localStorage.setItem('leximind_username', userName);
    }
    editingName = false;
  }

  function handleNameKeydown(e) {
    if (e.key === 'Enter') saveName();
    if (e.key === 'Escape') editingName = false;
  }

  function startGame(gameKey) {
    const game = GAMES[gameKey];
    if (game) {
      currentGame = gameKey;
      inputMessage = game.prompt;
      sendMessage();
    }
  }

  async function sendMessage() {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    inputMessage = '';

    messages = [...messages, { role: 'user', content: userMessage }];
    scrollToBottom();
    isLoading = true;

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, session_id: sessionId })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';
      let started = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) {
                fullContent += data.token;
                if (!started) {
                  started = true;
                  messages = [...messages, { role: 'assistant', content: fullContent }];
                } else {
                  messages[messages.length - 1] = { ...messages[messages.length - 1], content: fullContent };
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
    } catch {
      messages = [...messages, { role: 'assistant', content: '\u00a1Ups! Algo sali\u00f3 mal. Int\u00e9ntalo de nuevo.' }];
    } finally {
      isLoading = false;
      scrollToBottom();
    }
  }

  function scrollToBottom() {
    if (messagesContainer) {
      setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }, 10);
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es', { month: 'short', day: 'numeric' });
  }

  function getInitial(str) {
    return str ? str.charAt(0).toUpperCase() : 'A';
  }
</script>

<div class="flex h-screen bg-gradient-to-br from-violet-100 via-purple-50 to-fuchsia-100 text-gray-800 overflow-hidden">
  {#if sidebarOpen}
    <div class="fixed inset-0 bg-black/50 z-40 lg:hidden" role="button" tabindex="0" onkeydown={() => {}} onclick={toggleSidebar}></div>
    <aside class="fixed lg:relative z-40 w-64 h-full bg-white/90 backdrop-blur-sm border-r border-violet-200 flex flex-col shadow-xl">
      <div class="p-4 border-b border-violet-100">
        <button
          onclick={startNewChat}
          class="w-full py-3 px-4 bg-gradient-to-r from-violet-400 to-purple-400 hover:from-violet-500 hover:to-purple-500 text-white rounded-xl font-bold transition-all transform hover:scale-105 shadow-lg cursor-pointer flex items-center justify-center gap-2"
        >
          <Sparkles class="w-4 h-4" />
          Nuevo chat
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-3">
        {#each sessions as session}
          <div class="group relative mb-2">
            <button
              onclick={() => { loadHistory(session.session_id); sidebarOpen = false; }}
              class="w-full text-left p-3 rounded-xl transition-all cursor-pointer {sessionId === session.session_id ? 'bg-violet-100 border-2 border-violet-300' : 'hover:bg-violet-50 border-2 border-transparent'}"
            >
              <div class="text-sm font-medium text-gray-700 truncate pr-6">{session.title || 'Chat'}</div>
              <div class="text-xs text-gray-400 mt-1">{formatDate(session.last_activity)}</div>
            </button>
            <button
              onclick={(e) => deleteSession(session.session_id, e)}
              class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-red-100 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
              aria-label="Eliminar chat"
            >
              <Trash2 class="w-4 h-4 text-red-400" />
            </button>
          </div>
        {/each}
      </div>

    </aside>
  {/if}

  <main class="flex-1 flex flex-col">
    <header class="bg-white/80 backdrop-blur-sm border-b border-violet-200 p-4 flex items-center justify-between shadow-sm">
      <div class="flex items-center gap-3">
        <button
          onclick={toggleSidebar}
          class="p-2 hover:bg-violet-100 rounded-xl transition-colors cursor-pointer"
          aria-label="Toggle sidebar"
        >
          <PanelLeft class="w-6 h-6 text-violet-600" />
        </button>
        <div class="flex items-center gap-2">
          <Brain class="w-8 h-8 text-violet-600" stroke-width="1.5" />
          <span class="font-black text-xl bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">LEXIMIND</span>
        </div>
      </div>

      <div class="flex items-center gap-3">
        {#if editingName}
          <input
            type="text"
            bind:value={tempName}
            onkeydown={handleNameKeydown}
            onblur={saveName}
            class="bg-violet-50 border-2 border-violet-300 rounded-xl px-3 py-1.5 text-sm text-gray-700 outline-none focus:border-violet-500 w-32"
          />
        {:else}
          <button
            onclick={startEditName}
            class="flex items-center gap-2 px-3 py-1.5 hover:bg-violet-100 rounded-xl text-sm transition-colors cursor-pointer font-medium"
          >
            <Smile class="w-5 h-5 text-violet-500" />
            <span>{userName}</span>
          </button>
        {/if}
      </div>
    </header>

    <div class="flex-1 overflow-y-auto p-4 md:p-6 scrollbar-thin" bind:this={messagesContainer}>
      {#if messages.length === 0}
        <div class="text-center px-4 pt-4 max-w-3xl mx-auto">
          <div class="mb-4 flex justify-center">
            <BrainCircuit class="w-16 h-16 text-violet-400" stroke-width="1.2" />
          </div>
          <h1 class="text-4xl font-black mb-4 bg-gradient-to-r from-violet-500 via-purple-500 to-fuchsia-500 bg-clip-text text-transparent">
            Hola! Soy LEXIMIND
          </h1>

          <div class="mb-6">
            <h2 class="text-lg font-bold text-gray-700 mb-3 flex items-center justify-center gap-2">
              <Sparkles class="w-5 h-5 text-violet-500" />
              Elige un tema
            </h2>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-2xl mx-auto">
              {#each Object.entries(GAMES) as [key, { title, prompt, icon: Icon }]}
                <button
                  onclick={() => startGame(key)}
                  class="p-4 bg-white rounded-2xl border-2 border-violet-200 hover:border-violet-400 shadow-md hover:shadow-xl transition-all transform hover:scale-105 cursor-pointer"
                >
                  <div class="mb-2 flex justify-center">
                    <Icon class="w-8 h-8 text-violet-600" />
                  </div>
                  <div class="font-bold text-sm text-violet-700">{title}</div>
                </button>
              {/each}
            </div>
          </div>
        </div>
      {/if}

      {#each messages as message}
        {#if message.role !== 'system'}
          <div class="flex gap-3 max-w-3xl mx-auto mb-4 {message.role === 'user' ? 'flex-row-reverse' : ''}">
            <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg {message.role === 'user' ? 'bg-gradient-to-br from-orange-300 to-pink-300' : 'bg-gradient-to-br from-violet-300 to-purple-300'}">
              {#if message.role === 'user'}
                <User class="w-5 h-5 text-white" />
              {:else}
                <BrainCircuit class="w-5 h-5 text-white" />
              {/if}
            </div>
            <div class="px-5 py-3 rounded-2xl max-w-[80%] shadow-md prose prose-sm max-w-none {message.role === 'user' ? 'bg-gradient-to-br from-orange-100 to-pink-100 text-gray-800 rounded-br-md border-2 border-orange-200' : 'bg-white text-gray-800 rounded-bl-md border-2 border-violet-200'}">
              {@html marked.parse(message.content)}
            </div>
          </div>
        {/if}
      {/each}

      {#if isLoading && messages.length > 0 && messages[messages.length - 1].role === 'user'}
        <div class="flex gap-3 max-w-3xl mx-auto mb-4 pl-14">
          <div class="flex gap-1">
            <span class="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce"></span>
            <span class="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></span>
            <span class="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></span>
          </div>
        </div>
      {/if}
    </div>

    <div class="p-4 bg-white/80 backdrop-blur-sm border-t border-violet-200">
      <div class="max-w-3xl mx-auto">
        <div class="flex gap-3 items-end">
          <textarea
            bind:value={inputMessage}
            placeholder="Pregunta cualquier cosa para aprender inglés"
            onkeydown={handleKeydown}
            disabled={isLoading}
            rows="1"
            class="flex-1 px-5 py-3 bg-white border-2 border-violet-300 rounded-2xl resize-none outline-none focus:border-violet-500 text-gray-700 placeholder-gray-400 transition-colors max-h-32 shadow-sm"
          ></textarea>

          <button
            onclick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            class="w-12 h-12 rounded-2xl bg-gradient-to-r from-violet-400 to-purple-400 text-white transition-all hover:from-violet-500 hover:to-purple-500 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex-shrink-0 flex items-center justify-center shadow-lg"
            aria-label="Enviar"
          >
            <Send class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </main>
</div>

<style>
  .scrollbar-thin::-webkit-scrollbar {
    width: 6px;
  }

  .scrollbar-thin::-webkit-scrollbar-track {
    background: transparent;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb {
    background: #a78bfa;
    border-radius: 3px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background: #8b5cf6;
  }

</style>
