'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Checkbox } from '@/components/ui/checkbox'
import { Database, Brain, Shield, TestTube, Plus, Trash2 } from 'lucide-react'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('connections')
  const queryClient = useQueryClient()

  // Queries
  const { data: connections } = useQuery({
    queryKey: ['connections'],
    queryFn: apiClient.getConnections,
  })

  const { data: policies } = useQuery({
    queryKey: ['policies'],
    queryFn: apiClient.getPolicies,
  })

  const { data: aiProviders } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: apiClient.getAIProviders,
  })

  // Mutations
  const testConnectionMutation = useMutation({
    mutationFn: apiClient.testConnection,
    onSuccess: () => {
      alert('Connection test successful!')
    },
    onError: (error: any) => {
      alert(`Connection test failed: ${error.message}`)
    }
  })

  const updatePoliciesMutation = useMutation({
    mutationFn: apiClient.updatePolicies,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      alert('Policies updated successfully!')
    }
  })

  // Mock data when API is not available
  const mockConnections = [
    {
      id: '1',
      name: 'Snowflake Production',
      type: 'snowflake',
      host: 'company.snowflakecomputing.com',
      database: 'PROD_DWH',
      status: 'connected',
      last_tested: '2025-01-09T10:00:00Z'
    },
    {
      id: '2',
      name: 'PostgreSQL Staging',
      type: 'postgresql',
      host: 'staging-db.company.com',
      database: 'staging',
      status: 'connected',
      last_tested: '2025-01-09T09:30:00Z'
    }
  ]

  const mockPolicies = {
    sql_preview_enabled: false,
    external_ai_enabled: false,
    pii_redaction_enabled: true,
    max_query_timeout: 300,
    max_sample_rows: 1000
  }

  const mockAIProviders = [
    {
      id: '1',
      name: 'Local Ollama',
      type: 'ollama',
      endpoint: 'http://localhost:11434',
      model: 'llama2',
      status: 'active'
    }
  ]

  const connectionsData = connections || mockConnections
  const policiesData = policies || mockPolicies
  const aiProvidersData = aiProviders || mockAIProviders

  const getConnectionIcon = (type: string) => {
    switch (type) {
      case 'snowflake': return '❄️'
      case 'postgresql': return '🐘'
      case 'mysql': return '🐬'
      case 'bigquery': return '📊'
      default: return '💾'
    }
  }

  const getStatusBadge = (status: string) => {
    const variants = {
      connected: 'bg-green-100 text-green-800',
      disconnected: 'bg-red-100 text-red-800',
      testing: 'bg-yellow-100 text-yellow-800',
    }
    return variants[status as keyof typeof variants] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between space-y-2 mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Configure connections, policies, and AI providers</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="connections">
            <Database className="mr-2 h-4 w-4" />
            Connections
          </TabsTrigger>
          <TabsTrigger value="policies">
            <Shield className="mr-2 h-4 w-4" />
            Policies
          </TabsTrigger>
          <TabsTrigger value="ai-providers">
            <Brain className="mr-2 h-4 w-4" />
            AI Providers
          </TabsTrigger>
        </TabsList>

        <TabsContent value="connections" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Data Connections</CardTitle>
                  <CardDescription>Manage your database and data warehouse connections</CardDescription>
                </div>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Connection
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {connectionsData.map((connection: any) => (
                  <div key={connection.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl">{getConnectionIcon(connection.type)}</div>
                      <div>
                        <h3 className="font-medium">{connection.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {connection.host} • {connection.database}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Last tested: {new Date(connection.last_tested).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge className={getStatusBadge(connection.status)}>
                        {connection.status}
                      </Badge>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => testConnectionMutation.mutate(connection)}
                        disabled={testConnectionMutation.isPending}
                      >
                        <TestTube className="mr-2 h-4 w-4" />
                        Test
                      </Button>
                      <Button variant="ghost" size="sm">
                        Edit
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="policies" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Security & Privacy Policies</CardTitle>
              <CardDescription>Configure data protection and access policies</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">SQL Preview</h4>
                      <p className="text-sm text-muted-foreground">
                        Allow users to preview generated SQL queries
                      </p>
                    </div>
                    <Checkbox 
                      checked={policiesData.sql_preview_enabled}
                      onCheckedChange={(checked) => {
                        updatePoliciesMutation.mutate({
                          ...policiesData,
                          sql_preview_enabled: checked
                        })
                      }}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">External AI Services</h4>
                      <p className="text-sm text-muted-foreground">
                        Enable external AI providers (OpenAI, Azure OpenAI, etc.)
                      </p>
                    </div>
                    <Checkbox 
                      checked={policiesData.external_ai_enabled}
                      onCheckedChange={(checked) => {
                        updatePoliciesMutation.mutate({
                          ...policiesData,
                          external_ai_enabled: checked
                        })
                      }}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">PII Redaction</h4>
                      <p className="text-sm text-muted-foreground">
                        Automatically redact personally identifiable information
                      </p>
                    </div>
                    <Checkbox 
                      checked={policiesData.pii_redaction_enabled}
                      onCheckedChange={(checked) => {
                        updatePoliciesMutation.mutate({
                          ...policiesData,
                          pii_redaction_enabled: checked
                        })
                      }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Max Query Timeout (seconds)</label>
                    <Input 
                      type="number" 
                      value={policiesData.max_query_timeout}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Max Sample Rows</label>
                    <Input 
                      type="number" 
                      value={policiesData.max_sample_rows}
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai-providers" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>AI Providers</CardTitle>
                  <CardDescription>Configure AI services for test generation and compilation</CardDescription>
                </div>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Provider
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {aiProvidersData.map((provider: any) => (
                  <div key={provider.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <Brain className="h-8 w-8 text-muted-foreground" />
                      <div>
                        <h3 className="font-medium">{provider.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {provider.type} • {provider.endpoint}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Model: {provider.model}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge className={getStatusBadge(provider.status === 'active' ? 'connected' : 'disconnected')}>
                        {provider.status}
                      </Badge>
                      <Button variant="outline" size="sm">
                        <TestTube className="mr-2 h-4 w-4" />
                        Test
                      </Button>
                      <Button variant="ghost" size="sm">
                        Edit
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>AI Configuration</CardTitle>
              <CardDescription>Global AI settings and preferences</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Default Temperature</label>
                  <Input type="number" step="0.1" min="0" max="2" defaultValue="0" className="mt-1" />
                  <p className="text-xs text-muted-foreground mt-1">
                    Controls randomness in AI responses (0 = deterministic, 2 = very creative)
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium">Max Tokens</label>
                  <Input type="number" defaultValue="2048" className="mt-1" />
                  <p className="text-xs text-muted-foreground mt-1">
                    Maximum number of tokens in AI responses
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="cache-responses" defaultChecked />
                  <label htmlFor="cache-responses" className="text-sm">Cache AI responses for similar queries</label>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
