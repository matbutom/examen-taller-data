const manifiestoTitulo = 'manifiesto del proyecto:';
const manifiestoTexto = 'este proyecto es la respuesta de los datos recopilados en torno a los hitos sociales en chile, y cuales eran los principales temas abordados en el estallido social y la pandemia. a raiz de eso se conforma este poema navegable, donde encontraras los datos, sus imagenes y sus clasificaciones ocultas.';

const colorsByTheme = {
  'Política': '#c81e1e',
  'Salud': '#1e8c5a',
  'Humor': '#d69312',
  'Economía': '#285ac8',
  'Espiritualidad': '#8c3cbe',
  'Cultura': '#c95a93',
  'Educación': '#646464'
};

const topPanel = document.querySelector('#topPanel');
const poem = document.querySelector('#poem');

let phraseEntries = [];
let mixedWords = [];
let hasEntered = false;
let shouldAnimatePoem = false;
let selectedWord = null;

init();

async function init() {
  topPanel.innerHTML = '<p class="loading">cargando poema...</p>';

  try {
    const response = await fetch('data/data.json');
    if (!response.ok) throw new Error('No se pudo leer data/data.json');

    const data = await response.json();
    phraseEntries = data.items
      .filter(item => item.palabras && item.palabras.trim())
      .map((item, phraseIndex) => ({
        item,
        phraseIndex,
        words: item.palabras.trim().split(/\s+/)
      }));
    mixedWords = shuffleWords(flattenWords(phraseEntries));

    render();
  } catch (error) {
    topPanel.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  }
}

function render() {
  document.documentElement.style.setProperty(
    '--active',
    selectedWord ? getThemeColor(selectedWord.item.tematica) : '#111111'
  );

  if (selectedWord) {
    renderSelection();
  } else {
    renderManifest();
  }

  renderPoem();
}

function renderManifest() {
  topPanel.innerHTML = `
    <button class="manifest-invitation" type="button" id="manifestInvitation">
      <span class="manifest-title">${manifiestoTitulo}</span>
      <span class="manifest-text">${manifiestoTexto}</span>
      <span class="manifest-cta">entrar al poema</span>
    </button>
  `;

  document.querySelector('#manifestInvitation').addEventListener('click', () => {
    hasEntered = true;
    shouldAnimatePoem = true;
    render();
  });
}

function renderSelection() {
  const { item, label } = selectedWord;
  const eventName = item.hito === 'Estallido' ? 'estallido social' : 'pandemia';
  const theme = item.tematica || 'sin dato';
  const percentage = item.porcentaje || 'sin dato';

  topPanel.innerHTML = `
    <article class="selection">
      <div class="image-box">
        <img src="${item.image}" alt="${escapeHtml(item.texto || label)}" />
      </div>
      <div class="selection-info">
        <h1 class="selected-word">${escapeHtml(label)}</h1>
        <div class="event-row" aria-label="Hito">
          <span class="event-pill ${item.hito === 'Estallido' ? 'active' : ''}">estallido social</span>
          <span class="event-pill ${item.hito === 'Pandemia' ? 'active' : ''}">pandemia</span>
        </div>
        <div class="data-block">
          <p class="data-sentence">
            esta palabra está dentro de
            <span>${escapeHtml(theme)}</span>,
            una temática que ocupa
            <span>${escapeHtml(percentage)}</span>
            del hito
            <span>${escapeHtml(eventName)}</span>.
          </p>
        </div>
        <button class="return-button" type="button" id="returnButton">volver al manifiesto</button>
      </div>
    </article>
  `;

  document.querySelector('#returnButton').addEventListener('click', () => {
    selectedWord = null;
    hasEntered = false;
    render();
  });
}

function renderPoem() {
  poem.innerHTML = '';
  poem.classList.toggle('is-revealed', hasEntered);
  poem.classList.toggle('is-entering', shouldAnimatePoem);

  if (!hasEntered) return;

  mixedWords.forEach((wordData, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = getWordClass(wordData);
    button.textContent = wordData.label;
    button.title = `${wordData.item.hito} · ${wordData.item.tematica} · ${wordData.item.porcentaje}`;
    button.style.setProperty('--delay', `${Math.min(index * 0.012, 1.8)}s`);
    button.addEventListener('click', () => {
      selectedWord = {
        item: wordData.item,
        phraseIndex: wordData.phraseIndex,
        wordIndex: wordData.wordIndex,
        key: wordData.key,
        label: wordData.label
      };
      render();
    });

    poem.appendChild(button);
    poem.appendChild(document.createTextNode(' '));
  });

  shouldAnimatePoem = false;
}

function getWordClass(wordData) {
  const classes = ['word-button'];
  if (!selectedWord) return classes.join(' ');

  if (wordData.phraseIndex === selectedWord.phraseIndex && wordData.wordIndex === selectedWord.wordIndex) {
    classes.push('selected');
  } else if (wordData.item.tematica === selectedWord.item.tematica) {
    classes.push('related');
  } else {
    classes.push('dimmed');
  }

  return classes.join(' ');
}

function flattenWords(entries) {
  return entries.flatMap(entry => entry.words.map((word, wordIndex) => ({
    item: entry.item,
    phraseIndex: entry.phraseIndex,
    wordIndex,
    key: normalizeWord(word),
    label: word
  })));
}

function shuffleWords(words) {
  const shuffled = [...words];

  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
  }

  return shuffled;
}

function normalizeWord(value) {
  return String(value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9ñ]/g, '');
}

function getThemeColor(theme) {
  return colorsByTheme[theme] || '#646464';
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
