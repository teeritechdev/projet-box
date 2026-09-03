(function() {
    'use strict';

    function initFilterBoxeursAdmin() {
        const selectCat = document.getElementById('id_categorie');
        const selectRouge = document.getElementById('id_boxeur_rouge');
        const selectBleu = document.getElementById('id_boxeur_bleu');

        if (!selectCat || (!selectRouge && !selectBleu)) return;

        function applyFilter() {
            const selectedCatId = selectCat.value;

            [selectRouge, selectBleu].forEach(selectElem => {
                if (!selectElem) return;
                const currentVal = selectElem.value;
                let currentValStillValid = false;

                Array.from(selectElem.options).forEach(opt => {
                    if (!opt.value) return; // Garder la ligne vide "---------"
                    
                    const catId = opt.getAttribute('data-categorie-id');
                    
                    // Si aucune catégorie sélectionnée, tout afficher.
                    // Si une catégorie est choisie, filtrer strictement sur la catégorie !
                    if (!selectedCatId || catId === selectedCatId) {
                        opt.style.display = '';
                        opt.disabled = false;
                        if (opt.value === currentVal) currentValStillValid = true;
                    } else {
                        opt.style.display = 'none';
                        opt.disabled = true;
                    }
                });

                if (!currentValStillValid && currentVal) {
                    selectElem.value = '';
                }
            });
        }

        selectCat.addEventListener('change', applyFilter);
        // Filtrer dès le chargement initial si une catégorie est déjà pré-sélectionnée
        applyFilter();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFilterBoxeursAdmin);
    } else {
        setTimeout(initFilterBoxeursAdmin, 300);
    }
})();
