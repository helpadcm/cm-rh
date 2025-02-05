document.addEventListener("DOMContentLoaded", function () {
    function calculateHours() {

        let entry = document.getElementById("entry_1")?.value;
        let out = document.getElementById("out_1")?.value;

        console.log("////////////////////////////////");
        console.log(entry);
        console.log(out);
        // if (entry && out) {
        //     let entryTime = entry/100;
        //     let outTime = out/100;
        //     let diff = outTime - entryTime; // Convierte a horas

        //     console.log(diff);

        // }
        document.getElementById("hours_worked").value = 0;
    }

    document.getElementById("entry_1")?.addEventListener("change", calculateHours);
    document.getElementById("out_1")?.addEventListener("change", calculateHours);
});
