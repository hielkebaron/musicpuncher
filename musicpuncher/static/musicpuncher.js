
function punch() {
    clearError()
    var input = document.getElementById('midiFileInput');
    if (!input.files[0]) {
        alert("No file selected");
    } else {
        var file = input.files[0];
        var fileName = $('.custom-file-label').text()
        var transpose = parseInt($('#transpose').val())
        var autofit = $('#autofit').is(":checked")
        var fr = new FileReader();
        fr.onload = function() {
            base64String = fr.result
                .replace('data:', '')
                .replace(/^.+,/, '');
            $.ajax("../api/punch", {
                data: JSON.stringify({
                    'midiFile': base64String,
                    'filename': fileName,
                    'transpose': transpose,
                    'autofit': autofit
                }),
                contentType: 'application/json',
                success: updateStatus,
                error: errorhandler,
                type: 'POST',
            })
        };
        fr.readAsDataURL(file);
    }
}

function test() {
    clearError()
    var input = document.getElementById('midiFileInput');
    if (!input.files[0]) {
        alert("No file selected");
    } else {
        var file = input.files[0];
        var fileName = $('.custom-file-label').text()
        var transpose = parseInt($('#transpose').val())
        var autofit = $('#autofit').is(":checked")
        var fr = new FileReader();
        fr.onload = function() {
            base64String = fr.result
                .replace('data:', '')
                .replace(/^.+,/, '');
            $.ajax("../api/punch?test=true", {
                data: JSON.stringify({
                    'midiFile': base64String,
                    'filename': fileName,
                    'transpose': transpose,
                    'autofit': autofit
                }),
                contentType: 'application/json',
                success: download,
                error: errorhandler,
                type: 'POST',
            })
        };
        fr.readAsDataURL(file);
    }
}

function download(base64String) {
    const url = window.URL.createObjectURL(base64toBlob(base64String));
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    // the filename you want
    a.download = 'puncher.mid';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}

function base64toBlob(b64Data, contentType='', sliceSize=512) {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
        const slice = byteCharacters.slice(offset, offset + sliceSize);

        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }

        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
    }

    const blob = new Blob(byteArrays, {type: contentType});
    return blob;
}

function stop() {
    $.ajax("../api/stop", {
        type: 'POST'
    })
}

function updateStatus() {
    $.ajax("../api/status", {
        error: function() {
            statusbadge = $("#statusbadge")
            statusbadge.attr('class', "badge badge-danger")
            statusbadge.text("Unable to get status")
        },
        success: function(data) {
            statusclasses = "badge badge-success"
            statustext = "Idle"
            filename = "None"

            if (data.active) {
                statusclasses = "badge badge-warning"
                statustext = "Punching"
                filename = data.file

                clearError()
                $("#inputpane").hide()
                $("#progresspane").show()
            } else {
                $("#inputpane").show()
                $("#progresspane").hide()
            }

            statusbadge = $("#statusbadge")
            statusbadge.attr('class', statusclasses)
            statusbadge.text(statustext)

            $("#filename").text(filename)
            progressbar = $("#progress")
            percentage = data.progress * 100
            progressbar.css("width", percentage + "%")
            progressbar.attr("aria-valuenow", Math.round(percentage))

            $("#stopbutton").prop('disabled', !data.active)
        }
    });
}

function clearError() {
    $("#error").hide()
}

function errorhandler(xhr, status, error) {
    message = xhr.responseText || error
    $("#error").text(`Error ${status}: ${message}`)
    $("#error").show()
}

$('#midiFileInput').on('change', function() {
    var fileName = $(this).val().replace("C:\\fakepath\\", "");
    $(this).next('.custom-file-label').html(fileName);
})

$("input[type='number']").inputSpinner()

$("#autofit").on('change', function() {
    $("#transpose").prop('disabled', !$(this).is(":checked"))
})

updateStatus();
setInterval(updateStatus, 2000);