/* ==========================================================
   QR DEL MENÚ
========================================================== */

const menuId =
    window.QR_MENU_ID;


/* ==========================================================
   INICIO
========================================================== */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadMenuQRs();

    }
);


/* ==========================================================
   CARGAR QRS
========================================================== */

async function loadMenuQRs() {

    const loading =
        document.getElementById(
            "qrLoading"
        );

    const grid =
        document.getElementById(
            "qrGrid"
        );

    const empty =
        document.getElementById(
            "qrEmpty"
        );

    const error =
        document.getElementById(
            "qrError"
        );


    try {

        const response =
            await fetch(
                `/api/menu/${menuId}/qrs`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "No fue posible generar los QRs."
            );

        }


        loading.style.display =
            "none";


        document.getElementById(
            "qrMenuTitle"
        ).textContent =
            data.menu.title;


        document.getElementById(
            "qrTotalTables"
        ).textContent =
            data.total_tables;


        document.getElementById(
            "qrDescription"
        ).textContent =
            `Se generaron ${data.total_tables} QR para las mesas activas.`;


        if (!data.tables.length) {

            empty.style.display =
                "flex";

            return;

        }


        grid.innerHTML =
            data.tables
                .map(
                    table =>
                        createQRCard(
                            data.menu,
                            table
                        )
                )
                .join("");


    }
    catch (err) {

        console.error(
            "Error cargando QRs:",
            err
        );


        loading.style.display =
            "none";


        error.style.display =
            "block";


        error.textContent =
            err.message ||
            "No fue posible cargar los QRs.";

    }

}


/* ==========================================================
   CREAR TARJETA
========================================================== */

function createQRCard(
    menu,
    table
) {

    return `

        <article
            class="qr-card"
        >

            <div class="qr-card-header">

                <div>

                    <span>
                        MESA
                    </span>

                    <h2>
                        ${escapeHtml(
                            String(
                                table.table_number
                            )
                        )}
                    </h2>

                </div>


                <span
                    class="qr-status"
                >
                    ACTIVA
                </span>

            </div>


            <div class="qr-image-container">

                <img
                    src="${table.qr_url}"
                    alt="QR Mesa ${escapeHtml(
                        String(
                            table.table_number
                        )
                    )}"
                    class="qr-image"
                >

            </div>


            <div class="qr-table-info">

                <strong>
                    ${escapeHtml(
                        table.table_name
                    )}
                </strong>

                <span>
                    ${
                        table.zone ||
                        "Salón"
                    }
                </span>

            </div>


            <div class="qr-url">

                /m/${escapeHtml(
                    String(
                        table.table_number
                    )
                )}

            </div>


            <div class="qr-card-actions">

                <button
                    type="button"
                    class="btn-primary"
                    onclick="printSingleQR(
                        '${escapeHtml(
                            String(
                                table.table_id
                            )
                        )}'
                    )"
                >
                    🖨 Imprimir QR
                </button>

            </div>

        </article>

    `;

}


/* ==========================================================
   IMPRIMIR UNO
========================================================== */

function printSingleQR(
    tableId
) {

    const image =
        document.querySelector(
            `.qr-card img[src*="/${tableId}/image"]`
        );


    if (!image) {

        alert(
            "No fue posible encontrar el QR."
        );

        return;

    }


    const card =
        image.closest(
            ".qr-card"
        );


    const printWindow =
        window.open(
            "",
            "_blank",
            "width=800,height=900"
        );


    printWindow.document.write(`

        <!DOCTYPE html>

        <html>

        <head>

            <title>
                QR Mesa
            </title>

            <style>

                body {
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: Arial, sans-serif;
                }

                .ticket {
                    width: 400px;
                    text-align: center;
                    padding: 40px;
                }

                img {
                    width: 320px;
                    height: 320px;
                }

                h1 {
                    margin-top: 25px;
                    font-size: 32px;
                }

                p {
                    color: #555;
                    font-size: 18px;
                }

                @media print {

                    body {
                        min-height: auto;
                    }

                }

            </style>

        </head>

        <body>

            <div class="ticket">

                ${card.innerHTML}

            </div>

            <script>

                window.onload = function() {

                    window.print();

                };

            <\/script>

        </body>

        </html>

    `);


    printWindow.document.close();

}


/* ==========================================================
   ESCAPAR HTML
========================================================== */

function escapeHtml(
    value
) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}