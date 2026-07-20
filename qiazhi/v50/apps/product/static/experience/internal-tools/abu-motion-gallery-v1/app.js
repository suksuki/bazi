const ROOT = "/assets/abu/v12-actor-pass/";
const gallery = document.querySelector("#gallery");
const template = document.querySelector("#motionCardTemplate");

function relativeAsset(path) {
  return `${ROOT}${path}`;
}

function toggleVideo(video, button) {
  if (video.paused) {
    video.play();
    button.textContent = "Ⅱ";
  } else {
    video.pause();
    button.textContent = "▶";
  }
}

function renderAction(action) {
  const fragment = template.content.cloneNode(true);
  const card = fragment.querySelector(".motion-card");
  const video = fragment.querySelector("video");
  const toggle = fragment.querySelector('[data-command="toggle"]');
  const restart = fragment.querySelector('[data-command="restart"]');
  card.dataset.actionId = action.action_id;
  video.src = relativeAsset(action.video);
  video.poster = relativeAsset(action.poster);
  video.style.setProperty("--motion-scale", String(action.display_scale || 1));
  fragment.querySelector(".family").textContent = action.action_family;
  fragment.querySelector(".motion-label").textContent = action.label_zh;
  fragment.querySelector(".action-id").textContent = action.action_id;
  fragment.querySelector(".description").textContent = action.description_zh;
  fragment.querySelector(".metadata").textContent = `${(action.duration_ms / 1000).toFixed(1)}s · ${action.facing} · ${action.loop_mode}`;
  fragment.querySelector(".product-role").textContent = `用途：${action.product_role}`;
  toggle.addEventListener("click", () => toggleVideo(video, toggle));
  restart.addEventListener("click", () => {
    video.currentTime = 0;
    video.play();
    toggle.textContent = "Ⅱ";
  });
  video.addEventListener("ended", () => { toggle.textContent = "▶"; });
  video.play().catch(() => { toggle.textContent = "▶"; });
  gallery.append(fragment);
}

async function init() {
  const response = await fetch(`${ROOT}library.json`, {cache: "no-store"});
  if (!response.ok) throw new Error(`motion_library_unavailable:${response.status}`);
  const library = await response.json();
  library.actions.forEach(renderAction);
  document.querySelectorAll('input[name="background"]').forEach((input) => {
    input.addEventListener("change", () => { gallery.dataset.background = input.value; });
  });
  window.getAbuMotionGalleryState = () => ({
    version: library.version,
    background: gallery.dataset.background,
    actions: library.actions.map((action) => action.action_id),
  });
}

init().catch((error) => {
  gallery.textContent = "Motion Library 暂时无法载入。";
  console.error(error);
});
