function createChart({canvasId, all_data, settings}) {
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

function getColors(start, end, numColors) {
    var start = 230
    var end = 0
    colors = []

    for (var i = 0; i < numColors; i++) {
        step_size = (start-end) / numColors
        var red = 255
        var green = start - i * step_size
        var blue = start - i * step_size
        colors.push(`rgb(${red}, ${green}, ${blue})`)
    }
    return colors
}


function createHorizontalBarChart({canvasId, all_data, settings}) {
    var data = {
        labels: all_data['labels'],
        datasets: [{
            label: 'Minutes in zone',
            data: all_data['values'],
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1,
            backgroundColor: getColors(233, 0, all_data['labels'].length),
        }]
    };

    var ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            indexAxis: 'y',
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Minutes",
                    },
                }
            }
        },

        responsive: true,
        plugins: {
          legend: {
            position: 'right',
          },
          title: {
            display: true,
            text: 'Chart.js Horizontal Bar Chart'
          }
        }
    });
}