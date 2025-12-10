/**
 * SIMULADOR DE DALTONISMO
 * Permite testar a interface com diferentes tipos de deficiência de visão de cores
 */

(function() {
    'use strict';
    
    // Tipos de daltonismo disponíveis
    const COLORBLIND_TYPES = {
        'none': {
            name: 'Visão Normal',
            description: 'Sem simulação',
            filter: null,
            prevalence: '~92% da população'
        },
        'protanopia': {
            name: 'Protanopia',
            description: 'Dificuldade com vermelho',
            filter: 'url(#protanopia-filter)',
            prevalence: '~1% dos homens'
        },
        'deuteranopia': {
            name: 'Deuteranopia',
            description: 'Dificuldade com verde',
            filter: 'url(#deuteranopia-filter)',
            prevalence: '~1% dos homens'
        },
        'tritanopia': {
            name: 'Tritanopia',
            description: 'Dificuldade com azul',
            filter: 'url(#tritanopia-filter)',
            prevalence: '~0.001% da população'
        },
        'protanomaly': {
            name: 'Protanomalia',
            description: 'Fraqueza com vermelho',
            filter: 'url(#protanomaly-filter)',
            prevalence: '~1% dos homens'
        },
        'deuteranomaly': {
            name: 'Deuteranomalia',
            description: 'Fraqueza com verde',
            filter: 'url(#deuteranomaly-filter)',
            prevalence: '~5% dos homens'
        },
        'tritanomaly': {
            name: 'Tritanomalia',
            description: 'Fraqueza com azul',
            filter: 'url(#tritanomaly-filter)',
            prevalence: '~0.01% da população'
        },
        'achromatopsia': {
            name: 'Acromatopsia',
            description: 'Visão em escala de cinza',
            filter: 'url(#achromatopsia-filter)',
            prevalence: '~0.003% da população'
        },
        'achromatomaly': {
            name: 'Acromatomalia',
            description: 'Fraqueza monocromática',
            filter: 'url(#achromatomaly-filter)',
            prevalence: '~0.001% da população'
        }
    };
    
    const STORAGE_KEY = 'colorblind-simulation-mode';
    let currentMode = 'none';
    
    /**
     * Inicializa o simulador
     */
    function initColorblindSimulator() {
        // Carregar filtros SVG
        loadSVGFilters();
        
        // Verificar modo salvo
        const savedMode = localStorage.getItem(STORAGE_KEY);
        if (savedMode && COLORBLIND_TYPES[savedMode]) {
            currentMode = savedMode;
            applyFilter(currentMode);
        }
        
        // Criar interface de controle (apenas em desenvolvimento)
        if (isDevelopmentMode()) {
            createControlPanel();
        }
        
        // Adicionar atalho de teclado (Ctrl+Alt+V)
        document.addEventListener('keydown', handleKeyboardShortcut);
    }
    
    /**
     * Carrega os filtros SVG na página
     */
    function loadSVGFilters() {
        // Verificar se já existe
        if (document.getElementById('colorblind-filters-svg')) {
            return;
        }
        
        // Carregar arquivo SVG
        fetch('/static/colorblind-filters.svg')
            .then(response => response.text())
            .then(svgContent => {
                const div = document.createElement('div');
                div.innerHTML = svgContent;
                div.style.display = 'none';
                document.body.insertBefore(div, document.body.firstChild);
            })
            .catch(error => {
                console.warn('Não foi possível carregar filtros de daltonismo:', error);
            });
    }
    
    /**
     * Aplica filtro de daltonismo
     */
    function applyFilter(type) {
        const filterInfo = COLORBLIND_TYPES[type];
        
        if (!filterInfo) {
            console.error('Tipo de daltonismo inválido:', type);
            return;
        }
        
        currentMode = type;
        
        // Aplicar filtro ao body
        if (filterInfo.filter) {
            document.body.style.filter = filterInfo.filter;
        } else {
            document.body.style.filter = 'none';
        }
        
        // Salvar preferência
        localStorage.setItem(STORAGE_KEY, type);
        
        // Atualizar interface
        updateControlPanel();
        
        // Anunciar mudança
        announceToScreenReader(`Simulação de ${filterInfo.name} ativada`);
    }
    
    /**
     * Cria painel de controle para testes
     */
    function createControlPanel() {
        // Verificar se já existe
        if (document.getElementById('colorblind-control-panel')) {
            return;
        }
        
        const panel = document.createElement('div');
        panel.id = 'colorblind-control-panel';
        panel.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 9998;
            background: white;
            border: 2px solid #333;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            max-width: 300px;
            font-family: sans-serif;
            font-size: 14px;
        `;
        
        panel.innerHTML = `
            <div style="margin-bottom: 12px; font-weight: bold; font-size: 16px;">
                🎨 Simulador de Daltonismo
            </div>
            <div style="margin-bottom: 8px; color: #666; font-size: 12px;">
                Teste a interface com diferentes tipos de visão de cores
            </div>
            <select id="colorblind-type-select" style="
                width: 100%;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                margin-bottom: 8px;
            ">
                ${Object.entries(COLORBLIND_TYPES).map(([key, info]) => `
                    <option value="${key}" ${key === currentMode ? 'selected' : ''}>
                        ${info.name} - ${info.description}
                    </option>
                `).join('')}
            </select>
            <div id="colorblind-info" style="
                font-size: 12px;
                color: #666;
                margin-top: 8px;
                padding: 8px;
                background: #f5f5f5;
                border-radius: 4px;
            "></div>
            <button id="colorblind-close" style="
                margin-top: 8px;
                padding: 6px 12px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            ">
                Fechar Painel
            </button>
        `;
        
        document.body.appendChild(panel);
        
        // Adicionar event listeners
        const select = document.getElementById('colorblind-type-select');
        select.addEventListener('change', (e) => {
            applyFilter(e.target.value);
        });
        
        const closeBtn = document.getElementById('colorblind-close');
        closeBtn.addEventListener('click', () => {
            panel.style.display = 'none';
        });
        
        // Atualizar informações
        updateControlPanel();
    }
    
    /**
     * Atualiza informações no painel de controle
     */
    function updateControlPanel() {
        const infoDiv = document.getElementById('colorblind-info');
        if (!infoDiv) return;
        
        const filterInfo = COLORBLIND_TYPES[currentMode];
        infoDiv.innerHTML = `
            <strong>${filterInfo.name}</strong><br>
            ${filterInfo.description}<br>
            <em>Prevalência: ${filterInfo.prevalence}</em>
        `;
    }
    
    /**
     * Manipula atalho de teclado (Ctrl+Alt+V)
     */
    function handleKeyboardShortcut(event) {
        if (event.ctrlKey && event.altKey && event.key === 'v') {
            event.preventDefault();
            
            // Mostrar/esconder painel
            const panel = document.getElementById('colorblind-control-panel');
            if (panel) {
                panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            } else if (isDevelopmentMode()) {
                createControlPanel();
            }
        }
    }
    
    /**
     * Verifica se está em modo de desenvolvimento
     */
    function isDevelopmentMode() {
        // Verificar se está em localhost ou tem parâmetro de debug
        return window.location.hostname === 'localhost' ||
               window.location.hostname === '127.0.0.1' ||
               window.location.search.includes('debug=true') ||
               window.location.search.includes('colorblind=true');
    }
    
    /**
     * Anuncia mensagem para leitores de tela
     */
    function announceToScreenReader(message) {
        let announcer = document.getElementById('colorblind-announcer');
        
        if (!announcer) {
            announcer = document.createElement('div');
            announcer.id = 'colorblind-announcer';
            announcer.setAttribute('role', 'status');
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            announcer.style.position = 'absolute';
            announcer.style.left = '-10000px';
            announcer.style.width = '1px';
            announcer.style.height = '1px';
            announcer.style.overflow = 'hidden';
            document.body.appendChild(announcer);
        }
        
        announcer.textContent = '';
        setTimeout(() => {
            announcer.textContent = message;
        }, 100);
    }
    
    /**
     * Remove todos os filtros
     */
    function removeAllFilters() {
        applyFilter('none');
    }
    
    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initColorblindSimulator);
    } else {
        initColorblindSimulator();
    }
    
    // Expor API pública
    window.ColorblindSimulator = {
        apply: applyFilter,
        remove: removeAllFilters,
        getCurrentMode: () => currentMode,
        getAvailableTypes: () => Object.keys(COLORBLIND_TYPES),
        showPanel: createControlPanel
    };
    
})();
