/** @odoo-module **/ // ¡Añade esta línea al principio!

console.log("¡Archivo de prueba cargado correctamente!");

// Esperar a que el documento esté completamente cargado
// document.addEventListener("DOMContentLoaded", function() {
//     var popup = document.getElementById("popupNotification");
//     if (popup) {
//         // Mostrar el popup
//         popup.style.display = "block";
//         // Ocultar el popup después de 5 segundos (por ejemplo)
//         setTimeout(function() {
//             popup.style.display = "none";
//         }, 5000); // 5000ms = 5 segundos
//     }
// });

document.addEventListener("DOMContentLoaded", function () {
    var absence_type = document.getElementById("absence_type");
    var vacDiv = document.getElementById("vac_div_id");
    var hcompDiv = document.getElementById("hcomp_div_id");
    var middleDayDiv = document.getElementById("middle_day_div_id");
    var periodDiv = document.getElementById("period_div_id");
    var middleDay = document.getElementById("middle_day");
    var finalDateDiv = document.getElementById("final_date_div");
    var finalDate = document.getElementById("final_date_id");
    var hoursRequest = document.getElementById("hours_request");
    var hoursDiv = document.getElementById("hours_div_id");
    var adjuntosDiv = document.getElementById("adjuntos_div");

    function setDefaultValues() {
        var selectedOption = absence_type.options[absence_type.selectedIndex];
        var type_code = selectedOption.getAttribute("data-opt-code");

        // Mostrar u ocultar VAC y HCOMP
        vacDiv.style.display = (type_code === "VAC") ? "block" : "none";
        hcompDiv.style.display = (type_code === "HCOMP") ? "block" : "none";

        // Mostrar u ocultar horas
        if (hoursRequest.checked) {
            hoursDiv.style.display = "block";
        } else {
            hoursDiv.style.display = "none";
        }

        // Lógica de finalDateDiv y periodDiv (según prioridad)
        if (hoursRequest.checked) {
            finalDateDiv.style.display = "none";
            finalDate.required = false;
            periodDiv.style.display = "none";
        } else if (middleDay.checked) {
            periodDiv.style.display = "block";
            finalDateDiv.style.display = "none";
            finalDate.required = false;
        } else {
            periodDiv.style.display = "none";
            finalDateDiv.style.display = "block";
            finalDate.required = true;
        }

        adjuntosDiv.style.display = (type_code === "PGS") ? "block" : "none";

    }

    setDefaultValues();
    absence_type.addEventListener("change", setDefaultValues);
    middleDay.addEventListener("change", setDefaultValues);
    hoursRequest.addEventListener("change", setDefaultValues);
});