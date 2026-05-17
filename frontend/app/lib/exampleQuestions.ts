export type ExampleCategoryId =
  | 'turkish'
  | 'modern'
  | 'ancient'
  | 'early_modern'

export interface ExampleCategory {
  id: ExampleCategoryId
  label: string
  examples: string[]
}

export const EXAMPLE_CATEGORIES: ExampleCategory[] = [
  {
    id: 'turkish',
    label: 'Turkish history',
    examples: [
      'What if Atatürk had lived until 1960?',
      'What if the Ottoman Empire had not entered World War I?',
      'What if the Siege of Vienna in 1683 had succeeded for the Ottomans?',
    ],
  },
  {
    id: 'modern',
    label: '20th century',
    examples: [
      'What if the Soviet Union had not collapsed in 1991?',
      'What if Germany had won World War II?',
      'What if the Cuban Missile Crisis had escalated into nuclear war?',
    ],
  },
  {
    id: 'early_modern',
    label: 'Early modern',
    examples: [
      'What if Napoleon had won the Battle of Waterloo?',
      'What if the American Revolution had failed?',
      'What if the Spanish Armada had defeated England in 1588?',
    ],
  },
  {
    id: 'ancient',
    label: 'Ancient & classical',
    examples: [
      'What if Julius Caesar had not been assassinated?',
      'What if Alexander the Great had lived another twenty years?',
      'What if the Library of Alexandria had never been destroyed?',
    ],
  },
]
