function initPreview() {

    const input = document.getElementById("image");

    if (!input) return;

    input.addEventListener("change", previewImage);

}

function previewImage(e) {

    const file = e.target.files[0];

    if (!file) return;

    const reader = new FileReader();

    reader.onload = function (event) {

        document.getElementById("previewImage").src =
            event.target.result;

    };

    reader.readAsDataURL(file);

}