document.addEventListener("DOMContentLoaded", () => {
    const statusEl = document.getElementById("chartStatus");
    const dotEl = document.getElementById("chartDot");

    if (!statusEl || !dotEl) {
        return;
    }

    const SYMBOLS = [
        {
            symbol: "BTCUSDT",
            priceId: "priceBTC",
            changeId: "changeBTC",
            volId: "volBTC"
        },
        {
            symbol: "ETHUSDT",
            priceId: "priceETH",
            changeId: "changeETH",
            volId: "volETH"
        }
    ];

    const POLL_MS = 1500;

    function setStatus(isAvailable) {
        if (isAvailable) {
            statusEl.textContent = "Live";
            dotEl.style.background = "";
            dotEl.style.boxShadow = "";
        } else {
            statusEl.textContent = "Live (unavailable)";
            dotEl.style.background = "#f87171";
            dotEl.style.boxShadow = "0 0 8px #f87171";
        }
    }

    function formatPrice(value) {
        return value.toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function formatVolume(value) {
        if (value >= 1e9) {
            return "$" + (value / 1e9).toFixed(2) + "B";
        }

        if (value >= 1e6) {
            return "$" + (value / 1e6).toFixed(2) + "M";
        }

        if (value >= 1e3) {
            return "$" + (value / 1e3).toFixed(2) + "K";
        }

        return "$" + value.toFixed(2);
    }

    async function fetchTicker(symbol) {
        const response = await fetch(
            `https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=${symbol}`
        );

        if (!response.ok) {
            throw new Error(`Bad response: ${response.status}`);
        }

        return response.json();
    }

    async function pollAll() {
        try {
            const results = await Promise.all(
                SYMBOLS.map((config) => fetchTicker(config.symbol))
            );

            results.forEach((data, index) => {
                const config = SYMBOLS[index];

                const price = parseFloat(data.lastPrice);
                const changePct = parseFloat(data.priceChangePercent);
                const volumeUsdt = parseFloat(data.quoteVolume);

                if (
                    Number.isNaN(price) ||
                    Number.isNaN(changePct) ||
                    Number.isNaN(volumeUsdt)
                ) {
                    throw new Error("Unexpected API payload");
                }

                const priceEl = document.getElementById(config.priceId);
                const changeEl = document.getElementById(config.changeId);
                const volumeEl = document.getElementById(config.volId);

                if (priceEl) {
                    priceEl.textContent = formatPrice(price);
                }

                if (changeEl) {
                    changeEl.textContent =
                        (changePct >= 0 ? "+" : "") +
                        changePct.toFixed(2) +
                        "%";

                    changeEl.classList.remove("up", "down");
                    changeEl.classList.add(
                        changePct >= 0 ? "up" : "down"
                    );
                }

                if (volumeEl) {
                    volumeEl.textContent = formatVolume(volumeUsdt);
                }
            });

            setStatus(true);
        } catch (error) {
            console.error("Failed to fetch market data:", error);
            setStatus(false);
        }
    }

    // Initial fetch
    pollAll();

    // Refresh every 5 seconds
    setInterval(pollAll, POLL_MS);
});