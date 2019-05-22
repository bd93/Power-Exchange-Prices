window.onload = function () {
    var ctx = document.getElementById('myChart').getContext('2d');
    //loading gif before socket message received
    //$('#loadingMessage').html('<img src="https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif" alt="">');
    window.myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: 24 }, (v, k) => k + 1),
            datasets: [],
        },
        options: {
            animation: {
                duration: 0
            },
            legend: {
                display: true,
                position: 'top',
                labels: {
                    fontColor: 'black'
                }
            },
            title: {
                display: true,
                text: 'Cene na berzama'
            },
            scales: {
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'eur/MWh'
                    }
                }],
                xAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'hour'
                    }
                }]
            }
        }
    })
}

function renderChart(data) {
    let label
    dataSets = {}
    date = data[0]["Publication_MarketDocument"]["TimeSeries"]["Period"]["timeInterval"]["end"]["$"]
    $("#date").text(function () {
        return "Dan: " + date.slice(0,-7)
    })
    for (let i = 0; i < data.length; i++) {
        let arrayPrices = []
        domain = data[i]["Publication_MarketDocument"]["TimeSeries"]["in_Domain.mRID"]["$"]
        arrayObjPrices = data[i]["Publication_MarketDocument"]["TimeSeries"]["Period"]["Point"]
        for (let i = 0; i < arrayObjPrices.length; i++) {
            arrayPrices.push(arrayObjPrices[i]["price.amount"]["$"])
        }
        switch (domain) {
            case "10YHU-MAVIR----U":
                label = "HUPEX";
                borderColor = "rgba(0, 170, 0, 1)";
                break;
            case "10YCS-SERBIATSOV":
                label = "SEEPEX";
                borderColor = "rgb(0, 154, 252, 1)";
                break;
            case "10YHR-HEP------M":
                label = "CROPEX";
                borderColor = "rgba(255, 255, 0, 1)";
                break;
            case "10YRO-TEL------P":
                label = "OPCOM";
                borderColor = "rgba(105, 105, 105, 1)";
                break;
            case "10YCA-BULGARIA-R":
                label = "IBEX";
                borderColor = "rgba(255, 153, 51, 1)";
                break;
        }
        let dataSet = {
            label: label,
            data: arrayPrices,
            borderColor: borderColor,
            backgroundColor: 'transparent',
            pointBorderColor: borderColor,
            pointBackgroundColor: borderColor,
            pointRadius: 5,
            pointHoverRadius: 10
        }
        if (window.myChart.data.datasets.length < data.length) {
            window.myChart.data.datasets.push(dataSet);
            dataSets[dataSet.label] = dataSet;
        }
        else {
            for (let i = 0; i < window.myChart.data.datasets.length; i++) {
                if (window.myChart.data.datasets[i].label == dataSet.label) {
                    window.myChart.data.datasets[i].data = dataSet.data;
                    dataSets[dataSet.label] = dataSet;
                }
            }
        }
    }
    window.myChart.update()
}

var clicked = {
    "SEEPEX": false,
    "HUPEX": false,
    "CROPEX": false,
    "OPCOM": false,
    "IBEX": false
}

function showOrRemoveData(event) {
    clicked[event.data.name] = !clicked[event.data.name]
    if (clicked[event.data.name] == true) {
        for (let i = 0; i < window.myChart.data.datasets.length; i++) {
            if (window.myChart.data.datasets[i].label == event.data.name) {
                window.myChart.data.datasets.splice(i, 1)
            }
        }
    }
    if (clicked[event.data.name] == false) {
        window.myChart.data.datasets.push(dataSets[event.data.name])
    }
    window.myChart.update()
}

$("#SEEPEX").bind('click', {name: "SEEPEX"}, showOrRemoveData)
$("#HUPEX").bind('click', {name: "HUPEX"}, showOrRemoveData)
$("#CROPEX").bind('click', {name: "CROPEX"}, showOrRemoveData)
$("#OPCOM").bind('click', {name: "OPCOM"}, showOrRemoveData)
$("#IBEX").bind('click', {name: "IBEX"}, showOrRemoveData)

var socket = new WebSocket(
    'ws://' + window.location.host + '/ws/prices/'
)

socket.onmessage = function (e) {
    //$('#loadingMessage').html('<img src="" alt="">');
    var data = e.data;
    data = JSON.parse(data);
    console.log("WebSocket message received:", data);
    renderChart(data)
}

socket.onclose = function (e) {
    console.log('WebSocket is closed now.')
}