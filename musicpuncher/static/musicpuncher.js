
function punch() {
    console.log("START PUNCHING!")

    var input = document.getElementById('midiFile');
    if (!input.files[0]) {
        alert("No file selected");
    } else {
        var file = input.files[0];
        var fr = new FileReader();
        fr.onload = function() {
            base64String = fr.result
                .replace('data:', '')
                .replace(/^.+,/, '');
            $.ajax("../api/punch", {
                data: JSON.stringify({'midiFile': base64String}),
                contentType: 'application/json',
                type: 'POST'
            })
        };
        fr.readAsDataURL(file);
    }
}

function stop() {
    $.ajax("../api/stop", {
        type: 'POST'
    })
}

function updateStatus() {
    $.ajax("../api/status", {
        success: function(data) {
            statusclasses = "badge badge-success"
            statustext = "Idle"
            if (data.active) {
                statusclasses = "badge badge-warning"
                statustext = "Active"
            }
            statusbadge = $("#statusbadge")
            statusbadge.attr('class', statusclasses)
            statusbadge.text(statustext)

            progressbar = $("#progress")
            percentage = Math.round(data.progress * 100)
            progressbar.css("width", percentage + "%")
            progressbar.attr("aria-valuenow", percentage)

            $("#stopbutton").prop('disabled', !data.active)
        }
    });
}

updateStatus();
setInterval(updateStatus, 2000);