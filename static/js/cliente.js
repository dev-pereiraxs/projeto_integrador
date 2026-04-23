<script>
    const cards = document.querySelectorAll('.preference-card');

    cards.forEach(card => {
        card.addEventListener('click', () => {
            card.classList.toggle('active');
        });
    });
</script>
