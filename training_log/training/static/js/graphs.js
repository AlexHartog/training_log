function createChart({canvasId, chartType, all_data, settings}) {
//     if (backgroundColor === undefined) {
//        backgroundColor = 'rgba(75, 192, 192, 0.2)'
//    }
//    if (borderColor == undefined) {
//        borderColor = 'rgba(75, 192, 192, 1)'
//    }
    console.log(all_data)

    labels = all_data[0].dates
    data_sets = []

    for (const item of all_data) {
        data_sets.push({label: item.user, data: item.values})
    }

    y_title = {}
    if ('y_label' in settings) {
        y_title = {
            display: true,
            text: settings['y_label']
        }
    }

    var ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: chartType,
        data: {
            labels: labels,
            datasets: data_sets,
        },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        parser: 'yyyy-MM-dd\'T\'HH:mm:ss',
                        displayFormats: {
                            day: 'dd-MM-yyyy'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date',
                    },
                },
                y: {
                    title: y_title
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        }

    });
}