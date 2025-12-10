/**
 * Lazy Loading para Imagens
 * Carrega imagens apenas quando estão prestes a entrar no viewport
 * Melhora performance inicial da página
 */

(function() {
    'use strict';

    // Configuração
    const config = {
        rootMargin: '50px', // Começa a carregar 50px antes de entrar no viewport
        threshold: 0.01,
        loadingClass: 'lazy-loading',
        loadedClass: 'lazy-loaded',
        errorClass: 'lazy-error'
    };

    /**
     * Carrega uma imagem
     */
    function loadImage(img) {
        const src = img.dataset.src;
        const srcset = img.dataset.srcset;

        if (!src) return;

        // Adicionar classe de loading
        img.classList.add(config.loadingClass);

        // Criar nova imagem para pré-carregar
        const tempImg = new Image();

        tempImg.onload = function() {
            // Aplicar src real
            img.src = src;
            if (srcset) {
                img.srcset = srcset;
            }

            // Remover atributos data
            delete img.dataset.src;
            delete img.dataset.srcset;

            // Atualizar classes
            img.classList.remove(config.loadingClass);
            img.classList.add(config.loadedClass);

            // Disparar evento customizado
            img.dispatchEvent(new CustomEvent('lazyloaded', {
                bubbles: true,
                detail: { src: src }
            }));
        };

        tempImg.onerror = function() {
            img.classList.remove(config.loadingClass);
            img.classList.add(config.errorClass);

            // Disparar evento de erro
            img.dispatchEvent(new CustomEvent('lazyerror', {
                bubbles: true,
                detail: { src: src }
            }));

            console.error('Erro ao carregar imagem lazy:', src);
        };

        // Iniciar carregamento
        tempImg.src = src;
        if (srcset) {
            tempImg.srcset = srcset;
        }
    }

    /**
     * Carrega imagem de background
     */
    function loadBackgroundImage(element) {
        const bg = element.dataset.bg;
        if (!bg) return;

        element.classList.add(config.loadingClass);

        // Criar imagem temporária para pré-carregar
        const tempImg = new Image();

        tempImg.onload = function() {
            element.style.backgroundImage = `url('${bg}')`;
            delete element.dataset.bg;

            element.classList.remove(config.loadingClass);
            element.classList.add(config.loadedClass);

            element.dispatchEvent(new CustomEvent('lazyloaded', {
                bubbles: true,
                detail: { bg: bg }
            }));
        };

        tempImg.onerror = function() {
            element.classList.remove(config.loadingClass);
            element.classList.add(config.errorClass);
            console.error('Erro ao carregar background lazy:', bg);
        };

        tempImg.src = bg;
    }

    /**
     * Inicializa Intersection Observer
     */
    function initLazyLoading() {
        // Verificar suporte ao Intersection Observer
        if (!('IntersectionObserver' in window)) {
            console.warn('IntersectionObserver não suportado. Carregando todas as imagens...');
            loadAllImages();
            return;
        }

        // Criar observer
        const observer = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const element = entry.target;

                    // Carregar imagem ou background
                    if (element.tagName === 'IMG') {
                        loadImage(element);
                    } else if (element.dataset.bg) {
                        loadBackgroundImage(element);
                    }

                    // Parar de observar este elemento
                    observer.unobserve(element);
                }
            });
        }, {
            rootMargin: config.rootMargin,
            threshold: config.threshold
        });

        // Observar todas as imagens lazy
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(function(img) {
            observer.observe(img);
        });

        // Observar todos os backgrounds lazy
        const lazyBackgrounds = document.querySelectorAll('[data-bg]');
        lazyBackgrounds.forEach(function(element) {
            observer.observe(element);
        });

        console.log(`Lazy loading inicializado: ${lazyImages.length} imagens, ${lazyBackgrounds.length} backgrounds`);
    }

    /**
     * Fallback: carrega todas as imagens imediatamente
     */
    function loadAllImages() {
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(loadImage);

        const lazyBackgrounds = document.querySelectorAll('[data-bg]');
        lazyBackgrounds.forEach(loadBackgroundImage);
    }

    /**
     * API pública
     */
    window.LazyLoader = {
        init: initLazyLoading,
        loadImage: loadImage,
        loadBackgroundImage: loadBackgroundImage,
        loadAll: loadAllImages
    };

    // Auto-inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLazyLoading);
    } else {
        initLazyLoading();
    }

})();
