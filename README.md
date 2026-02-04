# CoolStuff

CoolStuff is a collaborative platform for sharing and exploring **side interests** — the things we’re curious about outside of work or formal study. Think history rabbit holes, philosophy essays, tech trends, podcasts, videos, articles, or anything that made you stop and think: *“this is cool, others might like this too.”*

## Why this project exists

This project started from a simple problem:  
interesting content is often shared in group chats, but it quickly gets lost, buried, or mixed with things you don’t personally care about.

We wanted a space where:
- people can share things they genuinely find interesting  
- others can discover content based on **their own interests**
- exploration feels intentional, not overwhelming

Instead of one noisy feed, CoolStuff is built around **topics you choose**, so your feed reflects your curiosity.

## What CoolStuff is

CoolStuff is a web application where users can:
- share links to content related to their side interests  
- tag content with one or more topics (e.g. history, philosophy, technology)  
- subscribe to topics they care about  
- see a personalized feed based on those subscriptions  
- interact with content through bookmarks, upvotes, and comments  

The goal is not productivity or learning outcomes, but **curiosity, discovery, and conversation**.

## How we’re building it

The project is being developed step by step as a backend-first application.

Current stack:
- **FastAPI** for the backend
- **MongoDB** as the database
- Two separate databases:
  - one for **authentication**
  - one for **application data** (topics, resources, interactions)

The architecture follows best practices with clear separation between:
- API routes
- business logic
- database access
- schemas and models

This repository contains the backend setup and infrastructure, and will evolve as new features are added.

---

More documentation and implementation details will be added as the project grows.
