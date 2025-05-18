<template>
  <div>
    <h2>Reportes</h2>
    <form @submit.prevent="crearReporte">
      <input v-model="descripcion" placeholder="Descripción" required />
      <input v-model="fecha" type="date" required />
      <button type="submit">Enviar</button>
    </form>
    <ul>
      <li v-for="r in reportes" :key="r.id">{{ r.descripcion }} - {{ r.fecha }}</li>
    </ul>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      descripcion: '',
      fecha: '',
      reportes: []
    }
  },
  mounted() {
    this.cargarReportes()
  },
  methods: {
    async cargarReportes() {
      const res = await axios.get('http://localhost:3001/reportes')
      this.reportes = res.data
    },
    async crearReporte() {
      await axios.post('http://localhost:3001/reportes', {
        descripcion: this.descripcion,
        fecha: this.fecha
      })
      this.descripcion = ''
      this.fecha = ''
      this.cargarReportes()
    }
  }
}
</script>
