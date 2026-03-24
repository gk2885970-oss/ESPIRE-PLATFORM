const API_BASE = "http://localhost:8000";

// TEAM LOGIN
async function loginTeam() {
  const email = document.getElementById("team-email").value;
  const password = document.getElementById("team-password").value;

  const res = await fetch(`${API_BASE}/loginTeam`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();
  if (res.ok) {
    localStorage.setItem("teamToken", data.token);
    alert("Team login successful!");
    loadPosts();
  } else {
    alert(data.detail || "Team login failed");
  }
}

// ADMIN LOGIN
async function loginAdmin() {
  const email = document.getElementById("admin-email").value;
  const password = document.getElementById("admin-password").value;

  const res = await fetch(`${API_BASE}/loginAdmin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();
  if (res.ok) {
    localStorage.setItem("adminToken", data.token);
    alert("Admin login successful!");
    loadPosts();
  } else {
    alert(data.detail || "Admin login failed");
  }
}

// LOAD MATCHES
async function loadMatches() {
  const res = await fetch(`${API_BASE}/teams`);
  const matches = await res.json();

  const container = document.getElementById("matches-container");
  container.innerHTML = "";
  matches.forEach(m => {
    const div = document.createElement("div");
    div.className = "match";
    div.innerHTML = `<strong>${m.team_name}</strong> (ID: ${m.team_id})`;
    container.appendChild(div);
  });
}

// LOAD POSTS
async function loadPosts() {
  const res = await fetch(`${API_BASE}/community/posts`);
  const posts = await res.json();

  const container = document.getElementById("posts-container");
  container.innerHTML = "";
  posts.forEach(post => {
    const div = document.createElement("div");
    div.className = "post";
    div.innerHTML = `<strong>Match:</strong> ${post.match_id} <br> Created At: ${new Date(post.created_at).toLocaleString()}`;
    div.onclick = () => loadComments(post.id);
    container.appendChild(div);
  });
}

// LOAD COMMENTS
async function loadComments(postId) {
  const res = await fetch(`${API_BASE}/community/${postId}/comments`);
  const comments = await res.json();

  const container = document.getElementById("comments-container");
  container.innerHTML = "";
  comments.forEach(c => {
    const div = document.createElement("div");
    div.className = "comment";
    div.innerHTML = `<strong>${c.team_id || "Admin " + c.admin_id}:</strong> ${c.content} <br><small>${new Date(c.created_at).toLocaleString()}</small>`;
    container.appendChild(div);
  });

  document.getElementById("comments-section").style.display = "block";
  document.getElementById("comments-section").dataset.postId = postId;
}

// ADD TEAM COMMENT
async function addTeamComment() {
  const postId = document.getElementById("comments-section").dataset.postId;
  const content = document.getElementById("comment-input").value;

  const res = await fetch(`${API_BASE}/community/${postId}/team_comment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + localStorage.getItem("teamToken")
    },
    body: JSON.stringify({ content })
  });

  if (res.ok) {
    loadComments(postId);
    document.getElementById("comment-input").value = "";
  } else {
    alert("Failed to add team comment");
  }
}

// ADD ADMIN COMMENT
async function addAdminComment() {
  const postId = document.getElementById("comments-section").dataset.postId;
  const content = document.getElementById("comment-input").value;

  const res = await fetch(`${API_BASE}/community/${postId}/admin_comment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + localStorage.getItem("adminToken")
    },
    body: JSON.stringify({ content })
  });

  if (res.ok) {
    loadComments(postId);
    document.getElementById("comment-input").value = "";
  } else {
    alert("Failed to add admin comment");
  }
}


window.onload = loadPosts;

function logout() {
    
    localStorage.removeItem("teamToken");
    localStorage.removeItem("adminToken");
    
    alert("Logged out successfully.");
    
    window.location.reload();
}
