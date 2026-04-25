document.addEventListener('DOMContentLoaded', function () 
{ const modalEl = document.getElementById('detailImageModal'); 
const modalImage = modalEl.querySelector('.detail-modal-image'); 
document.querySelectorAll('.detail-image').forEach(function (image) 
{ image.addEventListener('click', function () { modalImage.src = image.dataset.fullSrc; }); });
 modalEl.addEventListener('hidden.bs.modal', function () { modalImage.src = ''; }); }); 