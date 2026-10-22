
    import gallery from '{{ .Gallery }}';

    const articleContent = document.querySelector('.article-content');
    const shouldLoad = articleContent && (articleContent.querySelectorAll('figure').length > 0 || articleContent.querySelectorAll('img.gallery-image').length > 0);
    
    if (shouldLoad) {
        gallery(articleContent);

        const PhotoSwipeLightbox = (await import("{{ .Lightbox | safeJS }}")).default;
        const styleHref = "{{ .Style | safeJS }}";

        const styleTag = document.createElement('link');
        styleTag.rel = 'stylesheet';
        styleTag.href = styleHref;
        document.head.appendChild(styleTag);

        const lightbox = new PhotoSwipeLightbox({
            gallerySelector: '.article-content',
            childSelector: 'figure a.image-link',
            pswpModule: () => import("{{ .Core | safeJS }}")
        });
        lightbox.init();
    }
