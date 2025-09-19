// Base URL de l'API FastAPI
const API_BASE = "http://127.0.0.1:8000";

const resultPanel = document.getElementById('resultPanel');

// Fonction utilitaire pour remplir un <select> simple (domaine / macro)
function populateSelect(selectEl, items, defaultText) {
    selectEl.innerHTML = "";
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = defaultText;
    selectEl.appendChild(defaultOption);

    if (!items || items.length === 0) return;

    items.forEach(item => {
        const option = document.createElement("option");
        option.value = item;   // valeur = libellé
        option.textContent = item;
        selectEl.appendChild(option);
    });
    selectEl.options.sort()
}

// Fonction utilitaire pour remplir un <select> compétences avec code OGR
function populateCompetences(selectEl, items, defaultText) {
    selectEl.innerHTML = "";
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = defaultText;
    selectEl.appendChild(defaultOption);

    if (!items || items.length === 0) return;

    items.forEach(item => {
        const option = document.createElement("option");
        option.value = item.code;       // valeur = code OGR
        option.textContent = item.libelle; // affichage = libellé
        selectEl.appendChild(option);
    });
    selectEl.options.sort()
}

// Charger domaines
async function loadDomaines() {
    try {
        const res = await fetch(`${API_BASE}/get_domaine_competence`, { method: "POST" });
        const data = await res.json();
        populateSelect(document.getElementById("select_domaineCompetence"), data.liste_domaine || [], "Sélectionnez votre domaine");
    } catch (err) {
        console.error("Erreur domaines :", err);
    }
}

// Charger macro-compétences
async function loadMacro(domain) {
    const macroSelect = document.getElementById("select_macroCompetence");
    const competenceSelect = document.getElementById("select_Competence");

    if (!domain) {
        populateSelect(macroSelect, [], "Sélectionnez votre macro-compétence");
        populateCompetences(competenceSelect, [], "Sélectionnez votre compétence");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/get_macro_competence`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ domaine_competence: domain })
        });
        const data = await res.json();
        populateSelect(macroSelect, data.liste_macro_competence || [], "Sélectionnez votre macro-compétence");
        populateCompetences(competenceSelect, [], "Sélectionnez votre compétence");
    } catch (err) {
        console.error("Erreur macro :", err);
    }
}

// Charger compétences avec code OGR
async function loadCompetences(macro) {
    const competenceSelect = document.getElementById("select_Competence");

    if (!macro) {
        populateCompetences(competenceSelect, [], "Sélectionnez votre compétence");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/get_competence`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ macro_competence: macro })
        });
        const data = await res.json();
        populateCompetences(competenceSelect, data.liste_competence || [], "Sélectionnez votre compétence");
    } catch (err) {
        console.error("Erreur compétences :", err);
    }
}

// Tableau pour codes OGR sélectionnés
let selectedSkillsCodes = [];

// Ajouter compétence sélectionnée
function addSelectedCompetence() {
    const competenceSelect = document.getElementById("select_Competence");
    const code = competenceSelect.value;
    const libelle = competenceSelect.options[competenceSelect.selectedIndex]?.text;

    if (!code || selectedSkillsCodes.includes(code)) return;

    selectedSkillsCodes.push(code);

    const skillsGrid = document.getElementById("skillsGrid");
    const skillItem = document.createElement("div");
    skillItem.classList.add("skill-tag");
    skillItem.textContent = libelle;
    skillItem.dataset.code = code;

    // Suppression au clic
    skillItem.addEventListener("click", () => {
        selectedSkillsCodes = selectedSkillsCodes.filter(c => c !== code);
        skillItem.remove();
    });

    skillsGrid.appendChild(skillItem);
    document.getElementById("predictBtn").disabled = false;
}

// Listeners DOM
document.addEventListener("DOMContentLoaded", () => {
    loadDomaines();

    const domaineSelect = document.getElementById("select_domaineCompetence");
    const macroSelect = document.getElementById("select_macroCompetence");
    const addSkillBtn = document.getElementById("addSkillBtn");

    domaineSelect.addEventListener("change", () => loadMacro(domaineSelect.value));
    macroSelect.addEventListener("change", () => loadCompetences(macroSelect.value));
    addSkillBtn.addEventListener("click", addSelectedCompetence);

    // Prédiction
    document.getElementById("predictBtn").addEventListener("click", async () => {
        if (selectedSkillsCodes.length === 0) {
            alert("Veuillez ajouter au moins une compétence !");
            return;
        }

        try {
            // selectedSkillsCodes = []
            // selectedSkillsCodes.push("100023");
            // selectedSkillsCodes.push("100023");
            // selectedSkillsCodes.push("118788");
            // selectedSkillsCodes.push("483361");
            // selectedSkillsCodes.push("122698");
            // selectedSkillsCodes.push("122575");
            const res = await fetch(`${API_BASE}/predict`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ skills: selectedSkillsCodes })
            });
            const data = await res.json();
            const resultPanelContent = document.getElementById('resultPanelContent');
            const resultPanelStatus = document.getElementById('resultStatus');
            // Remove all child item
            while (resultPanelContent.firstChild) {
                resultPanelContent.removeChild(resultPanelContent.firstChild);
                }
            // Add results
            if(data.result.status == 'ok'){
                resultPanelStatus.innerText = "Basé sur l'analyse de vos compétences sélectionnées";
                data.result.predictions.forEach(item => {
                    const predict_job = document.createElement("div");
                    //predict_job.className = "job-prediction";
                    predict_job.textContent = item?.libelle || "Aucun résultat";
                    resultPanelContent.appendChild(predict_job);
                    const predict_met_div = document.createElement("div");
                    predict_met_div.className = "confidence-meter";
                    resultPanelContent.appendChild(predict_met_div);
                    // Div confidence meter
                    const predict_confidence_span = document.createElement("span");
                    predict_confidence_span.textContent = "Indice de fiabilité:"
                    predict_met_div.appendChild(predict_confidence_span);
                    const predict_confidence_bar = document.createElement("div");
                    predict_confidence_bar.className = "confidence-bar";
                    predict_met_div.appendChild(predict_confidence_bar);
                    // Confidence bar
                    const predict_confidence = document.createElement("div");
                    predict_confidence.className = "confidence-fill";
                    const confidence = Math.round(item?.score * 100) || 0;
                    predict_confidence.style.width = confidence + "%";
                    predict_confidence_bar.appendChild(predict_confidence);
                    const predict_percent = document.createElement("span");
                    predict_percent.textContent = confidence + "%";
                    predict_met_div.appendChild(predict_percent);
                });
            }
            else{
                // Erreur de prédiction
                resultPanelStatus.innerText = "Aucun métier trouvé: " + data.result.reason;
            }

        } catch (err) {
            console.error("Erreur prédiction :", err);
        }

        resultPanel.classList.add('show');
    });
});