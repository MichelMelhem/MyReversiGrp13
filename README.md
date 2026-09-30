# My Reversi (Group 13)

Welcome to the **My Reversi** project repository! This project is a domain-based implementation of the classic board game Reversi (Othello).

## Project Documentation
* **[reversi_domain.puml](./reversi_domain.puml):** The PlantUML source code for our primary domain class diagram.
* **[CRC_Cards_Google_Docs_Format.md](./CRC_Cards_Google_Docs_Format.md):** The Class Responsibility Collaboration (CRC) cards, formatted for easy integration into Google Docs.

## Architecture Overview
The current domain model focuses exclusively on core game logic (without networking components) and consists of the following primary classes:
1. `Game` - Core game loop and state management
2. `Board` - 8x8 grid management and placement rules
3. `Cell` - Individual grid coordinates
4. `Piece` - The game tokens
5. `Player` - Abstract participant
6. `HumanPlayer` - Human interface interactions
7. `ComputerPlayer` - AI opponent heuristics
