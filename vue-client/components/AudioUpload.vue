<template>
  <div class="audio-upload">
    <h1>Audio Upload</h1>

    <input type="file" @change="onFileSelected" accept="audio/*" />

    <button @click="uploadFile" :disabled="!selectedFile">Upload</button>

    <div v-if="response">
      <h3>Response:</h3>
      <pre>{{ response }}</pre>
    </div>

    <div v-if="error" style="color: red;">
      <h3>Error:</h3>
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      selectedFile: null,
      response: null,
      error: null,
    };
  },
  methods: {
    onFileSelected(event) {
      this.selectedFile = event.target.files[0];
    },
    async uploadFile() {
      if (!this.selectedFile) {
        this.error = "Please select a file to upload.";
        return;
      }
      const formData = new FormData();
      formData.append("file", this.selectedFile);

      try {
        this.error = null;
        this.response = null;

        const res = await axios.post("http://127.0.0.1:8000/upload-audio/", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
        this.response = res.data;
      } catch (err) {
        this.error = err.response?.data || "An error occurred.";
      }
    },
  },
};
</script>

<style>
.audio-upload {
  max-width: 400px;
  margin: 20px auto;
  text-align: center;
}
button {
  margin-top: 10px;
}
pre {
  text-align: left;
  background-color: #f4f4f4;
  padding: 10px;
  border-radius: 5px;
}
</style>
