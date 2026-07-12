document.addEventListener("DOMContentLoaded", function () {
    const modalEl = document.getElementById("detailImageModal");
    const triggerImages = Array.from(document.querySelectorAll(".detail-image"));

    if (!modalEl || triggerImages.length === 0) {
        return;
    }

    const modalImage = modalEl.querySelector(".detail-modal-image");
    const modalFrame = modalEl.querySelector(".image-lightbox-frame");
    const prevButton = modalEl.querySelector(".image-lightbox-prev");
    const nextButton = modalEl.querySelector(".image-lightbox-next");
    const counter = modalEl.querySelector(".image-lightbox-counter");
    const carouselEl = document.getElementById("detailImagesCarousel");
    let currentIndex = 0;
    let touchStartX = 0;
    let touchStartY = 0;
    let touchStartTime = 0;
    let touchMode = null;
    let zoomScale = 1;
    let panX = 0;
    let panY = 0;
    let lastPanX = 0;
    let lastPanY = 0;
    let pinchStartDistance = 0;
    let pinchStartScale = 1;
    let pendingImageAnimation = false;
    let renderToken = 0;

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

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function getTouchDistance(touches) {
        const deltaX = touches[0].clientX - touches[1].clientX;
        const deltaY = touches[0].clientY - touches[1].clientY;

        return Math.hypot(deltaX, deltaY);
    }

    function clampPan() {
        if (!modalFrame || zoomScale <= 1) {
            panX = 0;
            panY = 0;
            return;
        }

        const maxPanX = (modalFrame.clientWidth * (zoomScale - 1)) / 2;
        const maxPanY = (modalFrame.clientHeight * (zoomScale - 1)) / 2;

        panX = clamp(panX, -maxPanX, maxPanX);
        panY = clamp(panY, -maxPanY, maxPanY);
    }

    function applyImageTransform() {
        clampPan();
        modalImage.style.setProperty("--lightbox-scale", zoomScale);
        modalImage.style.setProperty("--lightbox-x", `${panX}px`);
        modalImage.style.setProperty("--lightbox-y", `${panY}px`);
    }

    function resetImageTransform() {
        touchMode = null;
        zoomScale = 1;
        panX = 0;
        panY = 0;
        applyImageTransform();
    }

    function prepareImageAnimation(direction) {
        pendingImageAnimation = Boolean(direction);
        modalImage.classList.remove("is-animating");

        if (!direction) {
            modalImage.style.setProperty("--lightbox-enter-x", "0px");
            return;
        }

        const enterOffset = direction === "next" ? "42px" : "-42px";
        modalImage.style.setProperty("--lightbox-enter-x", enterOffset);
    }

    function addExitImage(direction) {
        if (!direction || !modalFrame || !modalImage.src || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            return;
        }

        const exitImage = modalImage.cloneNode(false);
        exitImage.className = "detail-modal-image-exit";
        exitImage.alt = "";
        exitImage.setAttribute("aria-hidden", "true");
        exitImage.style.setProperty("--lightbox-scale", zoomScale);
        exitImage.style.setProperty("--lightbox-x", `${panX}px`);
        exitImage.style.setProperty("--lightbox-y", `${panY}px`);
        exitImage.style.setProperty("--lightbox-exit-x", direction === "next" ? "-42px" : "42px");

        modalFrame.appendChild(exitImage);
        exitImage.addEventListener("animationend", function () {
            exitImage.remove();
        }, { once: true });
    }

    function swapImage(image, direction) {
        prepareImageAnimation(direction);
        addExitImage(direction);
        resetImageTransform();
        modalImage.classList.remove("is-loaded");
        modalImage.src = image.src;
        modalImage.alt = image.alt;
    }

    function renderImage(index, direction) {
        const nextIndex = (index + images.length) % images.length;
        const image = images[nextIndex];
        const token = renderToken + 1;

        renderToken = token;
        currentIndex = nextIndex;

        if (counter) {
            counter.textContent = `${currentIndex + 1} / ${images.length}`;
        }

        syncCarousel(currentIndex);

        if (!direction) {
            swapImage(image);
            return;
        }

        const preloadImage = new Image();

        preloadImage.addEventListener("load", function () {
            if (token !== renderToken) {
                return;
            }

            swapImage(image, direction);
        }, { once: true });

        preloadImage.addEventListener("error", function () {
            if (token !== renderToken) {
                return;
            }

            swapImage(image, direction);
        }, { once: true });

        preloadImage.src = image.src;
    }

    function goToPrevious() {
        renderImage(currentIndex - 1, "previous");
    }

    function goToNext() {
        renderImage(currentIndex + 1, "next");
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

        if (pendingImageAnimation) {
            modalImage.classList.add("is-animating");
            pendingImageAnimation = false;
        }
    });

    modalImage.addEventListener("animationend", function () {
        modalImage.classList.remove("is-animating");
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
        if (window.matchMedia("(max-width: 767.98px)").matches) {
            return;
        }

        const clickedEmptyLightboxArea = event.target.classList.contains("image-lightbox-body") ||
            event.target.classList.contains("image-lightbox-frame");

        if (clickedEmptyLightboxArea) {
            closeLightbox();
        }
    });

    modalEl.addEventListener("touchstart", function (event) {
        if (event.touches.length === 2) {
            event.preventDefault();
            touchMode = "pinch";
            pinchStartDistance = getTouchDistance(event.touches);
            pinchStartScale = zoomScale;
            touchStartTime = 0;
            return;
        }

        if (event.touches.length !== 1) {
            return;
        }

        touchStartX = event.touches[0].clientX;
        touchStartY = event.touches[0].clientY;
        touchStartTime = Date.now();

        if (zoomScale > 1) {
            touchMode = "pan";
            lastPanX = touchStartX;
            lastPanY = touchStartY;
        } else {
            touchMode = "swipe";
        }
    }, { passive: false });

    modalEl.addEventListener("touchmove", function (event) {
        if (touchMode === "pinch" && event.touches.length === 2 && pinchStartDistance > 0) {
            event.preventDefault();
            zoomScale = clamp(pinchStartScale * (getTouchDistance(event.touches) / pinchStartDistance), 1, 4);
            applyImageTransform();
            return;
        }

        if (touchMode === "pan" && event.touches.length === 1) {
            event.preventDefault();
            panX += event.touches[0].clientX - lastPanX;
            panY += event.touches[0].clientY - lastPanY;
            lastPanX = event.touches[0].clientX;
            lastPanY = event.touches[0].clientY;
            applyImageTransform();
        }
    }, { passive: false });

    modalEl.addEventListener("touchend", function (event) {
        if (touchMode === "pinch") {
            if (event.touches.length < 2) {
                touchMode = null;
                pinchStartDistance = 0;
            }
            return;
        }

        if (touchMode === "pan") {
            if (zoomScale <= 1) {
                resetImageTransform();
            }
            touchMode = null;
            return;
        }

        if (images.length <= 1 || touchMode !== "swipe" || touchStartTime === 0 || event.changedTouches.length !== 1) {
            touchMode = null;
            return;
        }

        const touch = event.changedTouches[0];
        const deltaX = touch.clientX - touchStartX;
        const deltaY = touch.clientY - touchStartY;
        const elapsed = Date.now() - touchStartTime;
        const isHorizontalSwipe = Math.abs(deltaX) > 55 && Math.abs(deltaX) > Math.abs(deltaY) * 1.4;

        touchStartTime = 0;
        touchMode = null;

        if (!isHorizontalSwipe || elapsed > 700) {
            return;
        }

        if (deltaX < 0) {
            goToNext();
        } else {
            goToPrevious();
        }
    }, { passive: true });

    modalEl.addEventListener("touchcancel", function () {
        touchMode = null;
        touchStartTime = 0;
        pinchStartDistance = 0;
    });

    modalEl.addEventListener("shown.bs.modal", function () {
        modalEl.focus();
    });

    modalEl.addEventListener("hidden.bs.modal", function () {
        renderToken += 1;
        modalImage.src = "";
        modalImage.classList.remove("is-loaded", "is-animating");
        pendingImageAnimation = false;
        modalFrame.querySelectorAll(".detail-modal-image-exit").forEach(function (exitImage) {
            exitImage.remove();
        });
        resetImageTransform();
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
