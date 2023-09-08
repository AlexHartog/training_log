function createChart({canvasId, all_data, settings}) {
//     if (backgroundColor === undefined) {
//        backgroundColor = 'rgba(75, 192, 192, 0.2)'
//    }
//    if (borderColor == undefined) {
//        borderColor = 'rgba(75, 192, 192, 1)'
//    }
    console.log(all_data)

    dataSets = []

    for (const [key, value] of Object.entries(all_data)) {
        dataSets.push({label: key, data: value.y_values})
        labels = value.x_values
    }

    if ('title' in settings) {
        title = {
            display: true,
            text: settings['title']
        }
    } else {
        title = {}
    }

    if ('y_label' in settings) {
        yTitle = {
            display: true,
            text: settings['y_label']
        }
    } else {
        yTitle = {}
    }

    if ('chart_type' in settings) {
        chartType = settings['chart_type']
    } else {
        chartType = 'line'
    }

    if ('x_type' in settings) {
        xAxisType = settings['x_type']
    } else {
        xAxisType = 'time'
    }

    if ('x_label' in settings) {
        xLabel = settings['x_label']
    } else {
        xLabel = 'Date'
    }


    var ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: chartType,
        data: {
            labels: labels,
            datasets: dataSets,
        },
        options: {
            scales: {
                x: {
                    type: xAxisType,
                    time: {
                        parser: 'yyyy-MM-dd\'T\'HH:mm:ss',
                        displayFormats: {
                            day: 'dd-MM-yyyy'
                        }
                    },
                    title: {
                        display: true,
                        text: xLabel,
                    },
                },
                y: {
                    title: yTitle
                }
            },
            plugins: {
                legend: {
                    display: true
                },
                title: title,
            },
            responsive: true,
            maintainAspectRatio: false,
            elements: {
                point: {
                    radius: 0
                }
            }
        },
    });
}