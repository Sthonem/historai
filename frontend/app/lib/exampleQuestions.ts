export type ExampleCategoryId =
  | 'global_conflicts'
  | 'empires_states'
  | 'leaders_legacies'
  | 'ancient'

export interface ExampleCategory {
  id: ExampleCategoryId
  label: string
  examples: string[]
}

export const EXAMPLE_CATEGORIES: ExampleCategory[] = [
  {
    id: 'global_conflicts',
    label: 'Global conflicts',
    examples: [
      'What if the Ottoman Empire had not entered World War I?',
      'What if Germany had won World War II?',
      'What if the Cuban Missile Crisis had escalated into nuclear war?',
    ],
  },
  {
    id: 'empires_states',
    label: 'Empires & states',
    examples: [
      'What if the Soviet Union had not collapsed in 1991?',
      'What if the Siege of Vienna in 1683 had succeeded for the Ottomans?',
      'What if the American Revolution had failed?',
    ],
  },
  {
    id: 'leaders_legacies',
    label: 'Leaders & legacies',
    examples: [
      'What if Atatürk had lived until 1960?',
      'What if Napoleon had won the Battle of Waterloo?',
      'What if Julius Caesar had not been assassinated?',
    ],
  },
  {
    id: 'ancient',
    label: 'Ancient & classical',
    examples: [
      'What if Alexander the Great had lived another twenty years?',
      'What if the Library of Alexandria had never been destroyed?',
      'What if the Persian Empire had conquered Greece?',
    ],
  },
]
