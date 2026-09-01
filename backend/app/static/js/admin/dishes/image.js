function initPreview(){

    const input=document.getElementById("image");

    if(!input)return;

    input.addEventListener(

        "change",

        e=>{

            const file=e.target.files[0];

            if(!file)return;

            document.getElementById(

                "previewImage"

            ).src=URL.createObjectURL(file);

        }

    );

}