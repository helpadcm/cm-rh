/** @odoo-module **/

// console.log("¡Archivo de gastos de prueba cargado correctamente!");

const showFormInput = document.getElementById("id_show_form");
const formDivInput = document.getElementById("form_view_id");
const notFormDiv = document.getElementById("message_not_request_id");

const invoiceNumberInput = document.getElementById("invoice_number_record");

if (invoiceNumberInput) {

    function validateInvoiceNumber() {
        const pattern = /^\d{3}-\d{3}-\d{2}-\d{8}$/;

        if (pattern.test(invoiceNumberInput.value)) {
            invoiceNumberInput.classList.remove("is-invalid");
            invoiceNumberInput.classList.add("is-valid");
        } else {
            invoiceNumberInput.classList.remove("is-valid");
            invoiceNumberInput.classList.add("is-invalid");
        }
    }

    invoiceNumberInput.addEventListener("input", function (e) {
        let value = e.target.value.replace(/\D/g, '');

        value = value.substring(0, 16);

        let formatted = '';

        if (value.length > 0)
            formatted += value.substring(0, 3);

        if (value.length > 3)
            formatted += '-' + value.substring(3, 6);

        if (value.length > 6)
            formatted += '-' + value.substring(6, 8);

        if (value.length > 8)
            formatted += '-' + value.substring(8, 16);

        e.target.value = formatted;

        validateInvoiceNumber();
    });

    validateInvoiceNumber();
}

function setDefaultValues() {
    if (!showFormInput || !formDivInput || !notFormDiv) {
        return;
    }

    const show_form = showFormInput.value;
    // console.log(show_form)
    if (show_form === 'allow'){
        formDivInput.style.display = "block";
        notFormDiv.style.display = "none";
    }else{
        notFormDiv.style.display = "block";
        formDivInput.style.display = "none";
    }
}

// Asignar valores al cargar la página
if (document.getElementById("id_show_form")) {
    setDefaultValues();
}

// Asignar valores cuando cambien los datos
// amountInput.addEventListener("input", calculateAmounts);
// feesInput.addEventListener("change", calculateAmounts);