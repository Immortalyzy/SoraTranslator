<template>
    <span class="side-bar">
        <button v-for="button in buttons" :key="button.letter" :class="{ selected: button.letter === selectedButton }"
            @click="handleClick(button.letter)">
            {{ button.letter }}
        </button>
    </span>
</template>

<script>
export default {
    name: 'SideBar',
    data() {
        return {
            buttons: [
                { letter: "R", clicks: 0 },
                { letter: "T", clicks: 0 },
                { letter: "F", clicks: 0 },
            ],
            selectedButton: "T"
        }

    },
    methods: {
        handleClick(letter) {
            const button = this.buttons.find(b => b.letter === letter);
            button.clicks++;
            if (button.clicks === 1) {
                // reset the original selected button
                const selectedButton = this.buttons.find(b => b.letter === this.selectedButton);
                selectedButton.clicks = 0;
                this.selectedButton = letter;
                this.firstClickFunction(letter);
            } else if (button.clicks >= 2) {
                this.secondClickFunction(letter);
            }
        },
        firstClickFunction(letter) {
            console.log(`First function executed for ${letter}`);
            // write code here to change the content of Directory Tree
            this.$emit('change-tree', letter);
        },
        secondClickFunction(letter) {
            console.log(`Second function executed for ${letter}`);
            const selectedButton = this.buttons.find(b => b.letter === this.selectedButton);
            // if the clickes is a pair number, then hide the display of Directory Tree
            if (selectedButton.clicks % 2 === 0) {
                this.$emit('show-tree', false);
            } else {
                this.$emit('show-tree', true);
            }
        }
    }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Amatic+SC&display=swap');

button {
    margin: 0px 0px;
    padding: 0px 0px;
    /* sibar is 3vw */
    width: 2vw;
    height: 2vw;
    /* add minimum value*/
    min-width: 5px;
    min-height: 5px;
    font-size: large;
    align-items: center;
    display: inline-block;
    border: 1px solid #ffd0d0;
    background-color: rgb(179, 116, 0);
    color: rgb(255, 255, 255);
    text-align: center;
    text-decoration: none;
    font-family: Pacifico;
    transition: background-color 0.3s, border-color 0.3s, color 0.3s;
    text-shadow: 0 0 5px rgba(255, 0, 0, 0.7), 0 0 20px rgba(255, 0, 0, 0.6);
    /* Red glow */
}

button.selected {
    background-color: rgb(255, 255, 255);
    color: rgb(179, 116, 0);
    border: 1px solid rgb(179, 116, 0);
}
</style>
