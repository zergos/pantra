let spinnerCounter = -1;

function showSpinner() {
    spinnerCounter++;
    setTimeout(() => {
        if (spinnerCounter > 0) {
            document.getElementById('progress-spinner-animation').beginElement();
            document.getElementById('progress-spinner').style.display = 'block';
        }
    }, 100);
}

function hideSpinner() {
    spinnerCounter--;
    if (spinnerCounter <= 0) {
        spinnerCounter = 0;
        document.getElementById('progress-spinner-animation').endElement();
        document.getElementById('progress-spinner').style.display = 'none';
    }
}
