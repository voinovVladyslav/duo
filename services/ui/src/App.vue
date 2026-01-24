<script setup lang="ts">
import { ref } from 'vue'

const wsUrl = 'http://127.0.0.1:8000/ws'
const ws = ref<WebSocket | null>(null)

const connectToWs = () => {
    if (ws.value) {
        disconnect()
    }
    ws.value = new WebSocket(wsUrl)
    ws.value.addEventListener('message', (event) => {
        messages.value.push(event.data)
    })
}

const disconnect = () => {
    if (ws.value) {
        ws.value.close()
    }
}

const messages = ref<string[]>([])
</script>

<template>
    <h1>Home</h1>
    <button @click="connectToWs">Connect</button>
    <button @click="disconnect">Disconnect</button>
    <div>
        {{ messages }}
    </div>
</template>

<style scoped></style>
