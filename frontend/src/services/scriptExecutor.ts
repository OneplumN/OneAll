import { executeRepositoryScript, listRepositories, type ScriptRepository } from './codeRepositoryApi';

const repositoryCache = new Map<string, ScriptRepository>();
let repositoriesLoaded = false;

async function loadRepositories() {
  const repositories = await listRepositories();
  repositoryCache.clear();
  repositories.forEach((repo) => {
    repositoryCache.set(repo.name, repo);
    repo.tags?.forEach((tag) => {
      if (!repositoryCache.has(tag)) {
        repositoryCache.set(tag, repo);
      }
    });
  });
  repositoriesLoaded = true;
}

async function findRepository(label: string) {
  if (repositoryCache.has(label)) {
    return repositoryCache.get(label)!;
  }
  if (!repositoriesLoaded) {
    await loadRepositories();
    if (repositoryCache.has(label)) {
      return repositoryCache.get(label)!;
    }
  }
  await loadRepositories();
  const repo = repositoryCache.get(label);
  if (!repo) {
    throw new Error(`未找到名称或标签为「${label}」的脚本仓库`);
  }
  return repo;
}

export async function executeScriptByLabel(
  label: string,
  parameters?: Record<string, unknown>
) {
  const repository = await findRepository(label);
  return executeRepositoryScript(repository.id, { parameters });
}

export async function executeScriptById(
  repositoryId: string,
  parameters?: Record<string, unknown>
) {
  return executeRepositoryScript(repositoryId, { parameters });
}
