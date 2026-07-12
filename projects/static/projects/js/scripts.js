document.addEventListener("DOMContentLoaded", function () {
    const modalEl = document.getElementById("detailImageModal");
    const triggerImages = Array.from(document.querySelectorAll(".detail-image"));

    if (!modalEl || triggerImages.length === 0) {
        return;
    }

    const modalImage = modalEl.querySelector(".detail-modal-image");
    const prevButton = modalEl.querySelector(".image-lightbox-prev");
    const nextButton = modalEl.querySelector(".image-lightbox-next");
    const counter = modalEl.querySelector(".image-lightbox-counter");
    const carouselEl = document.getElementById("detailImagesCarousel");
    let currentIndex = 0;
    let touchStartX = 0;
    let touchStartY = 0;
    let touchStartTime = 0;

    const images = triggerImages.map(function (image, index) {
        return {
            src: image.dataset.fullSrc,
            alt: image.alt || "Project image",
            index: Number(image.dataset.lightboxIndex || index),
        };
    });

    function syncCarousel(index) {
        if (!carouselEl || !window.bootstrap) {
            return;
        }

        const carousel = bootstrap.Carousel.getOrCreateInstance(carouselEl);
        carousel.to(index);
    }

    function renderImage(index) {
        currentIndex = (index + images.length) % images.length;
        const image = images[currentIndex];

        modalImage.classList.remove("is-loaded");
        modalImage.src = image.src;
        modalImage.alt = image.alt;

        if (counter) {
            counter.textContent = `${currentIndex + 1} / ${images.length}`;
        }

        syncCarousel(currentIndex);
    }

    function goToPrevious() {
        renderImage(currentIndex - 1);
    }

    function goToNext() {
        renderImage(currentIndex + 1);
    }

    function closeLightbox() {
        if (!window.bootstrap) {
            return;
        }

        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) {
            modal.hide();
        }
    }

    triggerImages.forEach(function (image, index) {
        image.addEventListener("click", function () {
            renderImage(Number(image.dataset.lightboxIndex || index));
        });
    });

    modalImage.addEventListener("load", function () {
        modalImage.classList.add("is-loaded");
    });

    if (prevButton && nextButton) {
        const hasMultipleImages = images.length > 1;
        prevButton.hidden = !hasMultipleImages;
        nextButton.hidden = !hasMultipleImages;

        prevButton.addEventListener("click", goToPrevious);
        nextButton.addEventListener("click", goToNext);
    }

    modalEl.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            event.preventDefault();
            closeLightbox();
            return;
        }

        if (images.length <= 1) {
            return;
        }

        if (event.key === "ArrowLeft") {
            event.preventDefault();
            goToPrevious();
        }

        if (event.key === "ArrowRight") {
            event.preventDefault();
            goToNext();
        }
    });

    modalEl.addEventListener("click", function (event) {
        const clickedEmptyLightboxArea = event.target.classList.contains("image-lightbox-body") ||
            event.target.classList.contains("image-lightbox-frame");

        if (clickedEmptyLightboxArea) {
            closeLightbox();
        }
    });

    modalEl.addEventListener("touchstart", function (event) {
        if (images.length <= 1 || event.touches.length !== 1) {
            return;
        }

        touchStartX = event.touches[0].clientX;
        touchStartY = event.touches[0].clientY;
        touchStartTime = Date.now();
    }, { passive: true });

    modalEl.addEventListener("touchend", function (event) {
        if (images.length <= 1 || touchStartTime === 0 || event.changedTouches.length !== 1) {
            return;
        }

        const touch = event.changedTouches[0];
        const deltaX = touch.clientX - touchStartX;
        const deltaY = touch.clientY - touchStartY;
        const elapsed = Date.now() - touchStartTime;
        const isHorizontalSwipe = Math.abs(deltaX) > 55 && Math.abs(deltaX) > Math.abs(deltaY) * 1.4;

        touchStartTime = 0;

        if (!isHorizontalSwipe || elapsed > 700) {
            return;
        }

        if (deltaX < 0) {
            goToNext();
        } else {
            goToPrevious();
        }
    }, { passive: true });

    modalEl.addEventListener("shown.bs.modal", function () {
        modalEl.focus();
    });

    modalEl.addEventListener("hidden.bs.modal", function () {
        modalImage.src = "";
        modalImage.classList.remove("is-loaded");
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const slideshows = Array.from(document.querySelectorAll("[data-project-slideshow]"));
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (slideshows.length === 0 || prefersReducedMotion) {
        return;
    }

    slideshows.forEach(function (slideshow) {
        const slides = Array.from(slideshow.querySelectorAll(".project-card-slide"));

        if (slides.length <= 1) {
            return;
        }

        let currentIndex = slides.findIndex(function (slide) {
            return slide.classList.contains("is-active");
        });

        if (currentIndex < 0) {
            currentIndex = 0;
            slides[currentIndex].classList.add("is-active");
        }

        function showNextSlide() {
            slides[currentIndex].classList.remove("is-active");
            currentIndex = (currentIndex + 1) % slides.length;
            slides[currentIndex].classList.add("is-active");
        }

        let interval = null;

        function startSlideshow() {
            if (interval) {
                return;
            }

            interval = window.setInterval(showNextSlide, 3500);
        }

        function stopSlideshow() {
            if (!interval) {
                return;
            }

            window.clearInterval(interval);
            interval = null;
        }

        startSlideshow();

        slideshow.addEventListener("mouseenter", stopSlideshow);
        slideshow.addEventListener("mouseleave", startSlideshow);
        slideshow.addEventListener("focusin", stopSlideshow);
        slideshow.addEventListener("focusout", startSlideshow);
    });
});
