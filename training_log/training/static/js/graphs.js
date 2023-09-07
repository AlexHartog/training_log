function createChart({canvasId, chartType, labels, data, backgroundColor, borderColor}) {
     if (backgroundColor === undefined) {
        backgroundColor = 'rgba(75, 192, 192, 0.2)'
    }
    if (borderColor == undefined) {
        borderColor = 'rgba(75, 192, 192, 1)'
    }
    var ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: chartType,
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColor,
                borderColor: borderColor,
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        parser: 'YYYY-MM-DDTHH:mm:ss',
                        displayFormats: {
                            quarter: 'MMM YYYY'
                        }
                    }
                }
            }
            plugins: {
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: false,
                        },
                        pinch: {
                            enabled: false,
                        },
                        mode: 'xy',
                    },
                },
            },
        },
    });
}